"""GlomQuant Windows research release candidate. AGPL-3.0-or-later."""
import csv
import hashlib
import json
import os
import queue
import threading
import time
import traceback
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'model/best.pt'
VERSION = '0.1.0-rc1'
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'GlomQuant'
RESULTS = DATA / 'results'
DATA.mkdir(parents=True, exist_ok=True)
(DATA / 'ultralytics').mkdir(parents=True, exist_ok=True)
os.environ.setdefault('YOLO_CONFIG_DIR', str(DATA / 'ultralytics'))
os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
os.environ.setdefault('YOLO_OFFLINE', 'true')
MODEL_HASH = '98e9ce2434a3839e4dad168a114f48227b704fdc135adebcaa4ad00a4a7853aa'
SETTINGS = dict(confidence=.1, tile=1024, stride=768, imgsz=640,
                model_iou=.7, global_iou=.5, overlap_min_area=.5,
                tissue_skipping=False, color='RGB to BGR', device='cpu')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024*1024), b''): h.update(part)
    return h.hexdigest()

def write_json(path, data):
    temp = path.with_suffix('.partial.json')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

def extra_filter(merged):
    boxes = {i+1: r for i,r in enumerate(merged)}
    kept=[]; removed=[]
    for i in sorted(boxes, key=lambda i: (-boxes[i]['confidence'], i)):
        a=boxes[i]; reason=None
        for j in kept:
            b=boxes[j]
            inter=max(0,min(a['x2'],b['x2'])-max(a['x1'],b['x1']))*max(0,min(a['y2'],b['y2'])-max(a['y1'],b['y1']))
            ratio=inter/min(a['width']*a['height'], b['width']*b['height'])
            if ratio>.5:
                reason={'removed_id':i,'kept_id':j,'overlap':ratio};break
        if reason: removed.append(reason)
        else: kept.append(i)
    return [{'detection_id':i,**boxes[i]} for i in kept], removed

def saved_result(folder):
    c=json.loads((folder/'completion.json').read_text(encoding='utf-8'))
    conf=json.loads((folder/'run_config.json').read_text(encoding='utf-8'))
    if conf['model_sha256']!=MODEL_HASH: raise ValueError('Kayıt farklı bir modele ait.')
    if 'settings' in conf:
        if conf['settings']!=SETTINGS: raise ValueError('Kayıt farklı analiz ayarlarına ait.')
    else:
        for key in ['confidence','tile','stride','imgsz','model_iou','global_iou','tissue_skipping','color']:
            if conf.get(key)!=SETTINGS[key]: raise ValueError('Kayıt farklı analiz ayarlarına ait: '+key)
        if conf.get('extra_filter')!='intersection/min(area)>0.50; descending confidence, ascending detection_id':
            raise ValueError('Kayıt farklı tekrar filtresine ait.')
    for name,digest in c['outputs_sha256'].items():
        if Path(name).name != name: raise ValueError('Geçersiz sonuç dosyası adı.')
        if sha(folder/name)!=digest: raise ValueError('Sonuç dosyası değişmiş veya eksik: '+name)
    with (folder/'detections_filtered.csv').open(encoding='utf-8-sig') as f:
        count=sum(1 for _ in csv.DictReader(f))
    if count!=c['filtered_boxes']: raise ValueError('Kayıtlı sayı ile kutular uyuşmuyor.')
    return {'slide':c['slide'],'count':count,'seconds':c.get('inference_seconds'),'folder':str(folder),'reused':True}

def predict(model,slide,x,y):
    import numpy as np
    rgb=np.asarray(slide.read_region((x,y),0,(1024,1024)).convert('RGB'))
    r=model.predict(source=rgb[:,:,::-1].copy(),imgsz=640,conf=.1,iou=.7,device='cpu',verbose=False)[0]
    return [] if r.boxes is None else [(b.xyxy[0].cpu().numpy().tolist(),float(b.conf[0].item())) for b in r.boxes]

def reproduce(model):
    from self_check import verify_predictions
    return verify_predictions(model)


def environment_versions():
    from importlib.metadata import version
    return {name:version(name) for name in ['ultralytics','torch','torchvision','numpy','pillow','openslide-python','openslide-bin']}

def analyze(path,notify):
    start=time.perf_counter();path=Path(path)
    notify('Slayt kimliği kontrol ediliyor…',0)
    if path.suffix.lower() != '.svs' or not path.is_file(): raise ValueError('Mevcut bir .svs dosyası seçilmeli.')
    slide_hash=sha(path)
    if sha(MODEL)!=MODEL_HASH: raise ValueError('Model dosyasının kimliği değişmiş. Analiz başlatılmadı.')
    folder=RESULTS/slide_hash
    config={'model_sha256':MODEL_HASH,'slide_sha256':slide_hash,'settings':SETTINGS,'software_version':VERSION}
    if (folder/'completion.json').exists():
        if json.loads((folder/'run_config.json').read_text(encoding='utf-8'))!=config: raise ValueError('Kayıtlı analiz ayarları uyuşmuyor.')
        return saved_result(folder)
    if folder.exists():
        # Retain incomplete runs; never overwrite or reuse partial data silently.
        folder=RESULTS/(slide_hash+'_'+str(time.time_ns()))
    folder.mkdir(parents=True)
    write_json(folder/'run_config.json',config)
    notify('Model ve örnek kontrolü hazırlanıyor…',0)
    import openslide
    from ultralytics import YOLO, settings
    settings.update({'sync': False})
    import infer_wsi_pilot as pipeline
    model=YOLO(str(MODEL));reproduction_tiles=reproduce(model)
    raw=[]
    with openslide.OpenSlide(str(path)) as slide:
        w,h=slide.dimensions
        grid=[(x,y) for y in pipeline.starts(h,1024,768) for x in pipeline.starts(w,1024,768)]
        infer_start=time.perf_counter()
        for n,(x,y) in enumerate(grid,1):
            for box,c in predict(model,slide,x,y):
                x1,y1,x2,y2=max(0,min(x+box[0],w)),max(0,min(y+box[1],h)),max(0,min(x+box[2],w)),max(0,min(y+box[3],h))
                if x2<=x1 or y2<=y1:continue
                raw.append(dict(confidence=c,x1=x1,y1=y1,x2=x2,y2=y2,cx=(x1+x2)/2,cy=(y1+y2)/2,width=x2-x1,height=y2-y1,source_tile_x=x,source_tile_y=y))
            if n%10==0 or n==len(grid):notify(f'Slayt inceleniyor: %{100*n/len(grid):.0f}',100*n/len(grid))
        seconds=time.perf_counter()-infer_start
    notify('Tekrar kutuları birleştiriliyor ve sonuç kaydediliyor…',100)
    merged=pipeline.global_nms(raw,.5);filtered,audit=extra_filter(merged)
    pipeline.save_csv(folder/'detections_raw.csv',raw)
    pipeline.save_csv(folder/'detections_nms.csv',merged)
    fields=['detection_id','confidence','x1','y1','x2','y2','cx','cy','width','height','source_tile_x','source_tile_y']
    with (folder/'detections_filtered.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(filtered)
    features=[]
    for b in filtered:
        features.append({'type':'Feature','id':'PathAnnotationObject','properties':{'objectType':'annotation','name':f"B{b['detection_id']}",'classification':{'name':'Otomatik glomerul adayi','color':[0,180,100]},'detection_id':b['detection_id'],'confidence':b['confidence']},'geometry':{'type':'Polygon','coordinates':[[[b['x1'],b['y1']],[b['x2'],b['y1']],[b['x2'],b['y2']],[b['x1'],b['y2']],[b['x1'],b['y1']]]]}})
    write_json(folder/'MODEL_REVIEW.geojson',{'type':'FeatureCollection','features':features})
    write_json(folder/'filter_audit.json',audit)
    write_json(folder/'completion.json',{'slide':path.name,'status':'automatic_complete','filtered_boxes':len(filtered),'raw_boxes':len(raw),'inference_seconds':seconds,'wall_seconds_including_identity_setup_export':time.perf_counter()-start,'reproduction_tiles':reproduction_tiles,'software_version':VERSION,'environment':environment_versions(),'scope':'Automatic glomerular profile candidates; no medulla exclusion, no expert correction, no independent-test designation.','outputs_sha256':{n:sha(folder/n) for n in ['detections_raw.csv','detections_nms.csv','detections_filtered.csv','MODEL_REVIEW.geojson','filter_audit.json']}})
    result=saved_result(folder);result['reused']=False;return result

def analyze_in_process(path, notify):
    """Keep Tk and inference DLLs in separate processes, using the same runtime."""
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    proc=subprocess.Popen([sys.executable,'-u',str(HERE/'sayim_motoru.py'),str(path)],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,encoding='utf-8',errors='replace',creationflags=flags,
                          env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    result=None;failure=None;tail=[]
    try:
        for line in proc.stdout:
            tail.append(line.rstrip());tail=tail[-40:]
            if not line.startswith('GLOM_EVENT '):continue
            event=json.loads(line[len('GLOM_EVENT '):])
            if event['kind']=='progress':notify(event['text'],event['percent'])
            elif event['kind']=='result':result=event['result']
            elif event['kind']=='error':failure=event['detail']
        code=proc.wait()
    finally:
        proc.stdout.close()
        if proc.poll() is None:
            proc.terminate();proc.wait()
    if code!=0 or failure or result is None:
        raise RuntimeError(failure or ('Sayım motoru tamamlanamadı.\n'+'\n'.join(tail)))
    return result

def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    RESULTS.mkdir(parents=True, exist_ok=True)
    root=tk.Tk();root.title('GlomQuant — glomerül profili sayımı');root.geometry('780x520');root.minsize(700,480)
    frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Glomerül profili sayımı',font=('Segoe UI',22,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Slaytı seç → Analizi başlat → Sonucu gör',font=('Segoe UI',12)).pack(anchor='w',pady=(6,20))
    selected=tk.StringVar();ttk.Entry(frame,textvariable=selected,state='readonly').pack(fill='x')
    bar=ttk.Frame(frame);bar.pack(fill='x',pady=12)
    events=queue.Queue();state={'busy':False,'result':None}
    status=tk.StringVar(value='Bir .svs slaytı seç.');number=tk.StringVar(value='—')
    buttons=[]
    def busy(v):
        state['busy']=v
        for b in buttons:b.config(state='disabled' if v else 'normal')
    def job(fn):
        busy(True);state['result']=None;number.set('—');progress['value']=0
        def worker():
            try:events.put(('done',fn()))
            except Exception as e:
                log=DATA/('hata_'+str(time.time_ns())+'.txt');log.write_text(traceback.format_exc(),encoding='utf-8')
                events.put(('error',f'{e}\n\nAyrıntı kaydı: {log}'))
        threading.Thread(target=worker,daemon=True).start()
    def choose():
        f=filedialog.askopenfilename(title='Slayt seç',filetypes=[('SVS slayt','*.svs')])
        if f:selected.set(f);state['result']=None;number.set('—');status.set('Analizi başlatabilirsin.')
    def run():
        if not selected.get():messagebox.showinfo('Slayt seç','Önce bir .svs slaytı seç.');return
        path=selected.get()
        job(lambda:analyze_in_process(path,lambda text,p:events.put(('progress',(text,p)))))
    def previous():
        folder=filedialog.askdirectory(title='completion.json bulunan sonuç klasörünü seç',initialdir=str(RESULTS))
        if folder:job(lambda:saved_result(Path(folder)))
    for text,fn in [('Slayt seç',choose),('Analizi başlat',run),('Kayıtlı sonucu aç',previous)]:
        b=ttk.Button(bar,text=text,command=fn);b.pack(side='left',padx=(0,8));buttons.append(b)
    progress=ttk.Progressbar(frame,maximum=100);progress.pack(fill='x',pady=8)
    ttk.Label(frame,textvariable=status,wraplength=710).pack(anchor='w',pady=8)
    ttk.Label(frame,textvariable=number,font=('Segoe UI',32,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Otomatik glomerül profili adayı',font=('Segoe UI',12)).pack(anchor='w')
    def open_result():
        if state['result']:os.startfile(state['result']['folder'])
    ttk.Button(frame,text='Sonuç dosyalarını aç',command=open_result).pack(anchor='w',pady=14)
    ttk.Label(frame,text='Araştırma sürümü 0.1.0-rc1. Sayı otomatik çıktıdır; uzman düzeltmesi içermez.\nMedulla çizimi gerekmez. Yeni slayttaki doğruluk ayrıca değerlendirilmelidir.',wraplength=710).pack(anchor='w')
    def poll():
        try:
            while True:
                kind,data=events.get_nowait()
                if kind=='progress':status.set(data[0]);progress['value']=data[1]
                elif kind=='done':
                    busy(False);state['result']=data;number.set(str(data['count']));progress['value']=100
                    seconds=data['seconds'];duration=f' • Çıkarım: {seconds/60:.2f} dk' if seconds is not None else ''
                    status.set(f"{data['slide']} • "+('Kayıtlı sonuç açıldı; yeniden sayılmadı.' if data['reused'] else 'Analiz tamamlandı.')+duration)
                    if data['count']==0:messagebox.showinfo('Sıfır aday','Model bu slaytta aday bulamadı. Bu, dokuda glomerül olmadığını kanıtlamaz.')
                elif kind=='error':busy(False);status.set('Analiz tamamlanamadı; yeni sonuç oluşturulmadı.');messagebox.showerror('İşlem tamamlanamadı',data)
        except queue.Empty:pass
        root.after(150,poll)
    def close():
        if state['busy']:messagebox.showinfo('Analiz sürüyor','Analiz bitince pencereyi kapatabilirsin.');return
        root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);poll();root.mainloop()

if __name__=='__main__':main()
