"""Inference entry point: no Tk initialization, no background model imports."""
import json
import sys
import traceback
from app import analyze

def emit(kind, **data):
    print('GLOM_EVENT '+json.dumps({'kind':kind,**data},ensure_ascii=True),flush=True)

def main():
    try:
        if len(sys.argv)!=2:raise ValueError('Bir slayt dosyası seçilmeli.')
        result=analyze(sys.argv[1],lambda text,p:emit('progress',text=text,percent=p))
        emit('result',result=result)
        return 0
    except Exception:
        emit('error',detail=traceback.format_exc())
        return 1

if __name__=='__main__':sys.exit(main())
