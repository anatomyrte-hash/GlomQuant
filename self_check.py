"""Five historical, lossless reference tiles; no training or full-slide inference."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'GlomQuant'
os.environ.setdefault('YOLO_CONFIG_DIR',str(DATA/'ultralytics'))
os.environ.setdefault('YOLO_AUTOINSTALL','false')
os.environ.setdefault('YOLO_OFFLINE','true')
(DATA/'ultralytics').mkdir(parents=True,exist_ok=True)

def verify_predictions(model):
    import numpy as np
    from PIL import Image
    base=HERE/'examples/reference_tiles'
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    checked=[]
    for item in manifest['tiles']:
        path=base/item['image']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Örnek görüntü dosyası değişmiş: '+path.name)
        with Image.open(path) as image:
            rgb=np.asarray(image.convert('RGB'))
        result=model.predict(source=rgb[:,:,::-1].copy(),imgsz=640,conf=.1,iou=.7,device='cpu',verbose=False)[0]
        actual=[] if result.boxes is None else [(b.xyxy[0].cpu().numpy().tolist(),float(b.conf[0].item())) for b in result.boxes]
        remaining=list(item['expected'])
        if len(actual)!=len(remaining):
            raise ValueError(f"Örnek kontrolü uyuşmadı: {path.name}. Beklenen {len(remaining)}, bulunan {len(actual)}. Analiz başlatılmadı.")
        for box,confidence in actual:
            matches=[r for r in remaining if abs(r['confidence']-confidence)<manifest['confidence_tolerance'] and max(abs(a-b) for a,b in zip(r['xyxy'],box))<manifest['coordinate_tolerance_pixels']]
            if len(matches)!=1:
                raise ValueError('Örnek kontrolünde konum veya güven değeri uyuşmadı: '+path.name)
            remaining.remove(matches[0])
        checked.append(item['source_xy'])
    return checked

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    report={'version':'0.1.0-rc1','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'failed'}
    try:
        import openslide
        from tkinter import Tcl
        Tcl().eval('info patchlevel')
        from ultralytics import YOLO, settings
        settings.update({'sync':False})
        from app import MODEL,MODEL_HASH,sha,environment_versions
        if sha(MODEL)!=MODEL_HASH: raise ValueError('Model kimliği uyuşmuyor.')
        report['environment']=environment_versions()
        report['openslide_native_version']=openslide.__library_version__
        report['reproduction_tiles']=verify_predictions(YOLO(str(MODEL)))
        report['status']='passed'
        print('Örnek kontrolü başarılı. Beş görüntüde toplam 14 işaret, konumları ve güven değerleri kayıtla uyumlu.')
        print('Bu kontrol doğruluk ölçümü veya başka bilgisayarda doğrulama yerine geçmez.')
        return 0
    except Exception as exc:
        import traceback
        report['error']=str(exc)
        report['traceback']=traceback.format_exc()
        print(report['traceback'])
        return 1
    finally:
        path=DATA/'self_check.json'
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Kontrol kaydı: '+str(path))

if __name__=='__main__':sys.exit(main())
