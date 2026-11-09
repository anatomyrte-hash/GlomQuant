"""Compare a completed 59614 run with the historical automatic outputs."""
import csv
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def compare(folder):
    reference=ROOT/'examples/59614_automatic_reference'
    config=json.loads((folder/'run_config.json').read_text(encoding='utf-8'))
    target=json.loads((ROOT/'examples/full_slide_reference.json').read_text(encoding='utf-8'))
    if config['slide_sha256']!=target['sha256']:raise ValueError('Seçilen sonuç 59614 örnek slaytına ait değil.')
    expected_model=json.loads((ROOT/'provenance/model.json').read_text(encoding='utf-8'))
    if config['model_sha256']!=expected_model['sha256']:raise ValueError('Model kimliği uyuşmuyor.')
    if config.get('settings')!=expected_model['inference_settings']:raise ValueError('Analiz ayarları uyuşmuyor.')
    counts={}
    for name in ['detections_raw.csv','detections_nms.csv','detections_filtered.csv']:
        def read(base):
            with (base/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
        actual,expected=read(folder),read(reference)
        if len(actual)!=len(expected):raise ValueError(name+': kutu sayısı uyuşmuyor.')
        for a,b in zip(actual,expected):
            if set(a)!=set(b):raise ValueError(name+': sütunlar uyuşmuyor.')
            for key in a:
                tolerance=0 if key in ['detection_id','source_tile_x','source_tile_y'] else (0.0001 if key=='confidence' else 0.1)
                if abs(float(a[key])-float(b[key]))>tolerance:raise ValueError(name+': kutu konumu, sırası veya güven değeri uyuşmuyor.')
        counts[name]=len(actual)
    actual=json.loads((folder/'filter_audit.json').read_text(encoding='utf-8'))
    expected=json.loads((reference/'filter_audit.json').read_text(encoding='utf-8'))
    if len(actual)!=len(expected):raise ValueError('Filtre kararlarının sayısı uyuşmuyor.')
    for a,b in zip(actual,expected):
        if a['removed_id']!=b['removed_id'] or a['kept_id']!=b['kept_id'] or abs(a['overlap']-b['overlap'])>0.0001:
            raise ValueError('Filtre kararı uyuşmuyor.')
    geometry=json.loads((folder/'MODEL_REVIEW.geojson').read_text(encoding='utf-8'))['features']
    with (folder/'detections_filtered.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if len(geometry)!=len(rows):raise ValueError('GeoJSON kutu sayısı uyuşmuyor.')
    for feature,row in zip(geometry,rows):
        if feature['properties']['detection_id']!=int(row['detection_id']):raise ValueError('GeoJSON kutu kimliği uyuşmuyor.')
        coords=feature['geometry']['coordinates'][0]
        expected_coords=[[float(row[x]),float(row[y])] for x,y in [('x1','y1'),('x2','y1'),('x2','y2'),('x1','y2'),('x1','y1')]]
        if coords!=expected_coords:raise ValueError('GeoJSON koordinatları CSV ile uyuşmuyor.')
    return {'status':'passed','counts':counts,'scope':'Same automatic output within stated numerical tolerances; not expert accuracy.'}

def main():
    if len(sys.argv)>1:folder=Path(sys.argv[1])
    else:
        import tkinter as tk
        from tkinter import filedialog
        root=tk.Tk();root.withdraw()
        selected=filedialog.askdirectory(title='59614 sonucunun completion.json bulunan klasörünü seçin')
        root.destroy()
        if not selected:return
        folder=Path(selected)
    result=compare(folder)
    (folder/'reference_comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Karşılaştırma başarılı: ham kutular, son 768 kutu ve filtre kararları referansla uyumlu.')
    print('Bu otomatik çıktı karşılaştırmasıdır; gerçek glomerül sayısının doğrulaması değildir.')

if __name__=='__main__':
    try:main()
    except Exception as exc:print(str(exc));sys.exit(1)
