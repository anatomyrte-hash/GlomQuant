"""Use bundled Python to prepare a private environment; never alter system Python."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8',errors='replace')
sys.stderr.reconfigure(encoding='utf-8',errors='replace')

ROOT=Path(__file__).resolve().parents[1]
VENV=ROOT/'.venv'
PY=VENV/'Scripts/python.exe'
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'GlomQuant'
ENV={k:v for k,v in os.environ.items() if k.upper() not in ['PYTHONPATH','PYTHONHOME','VIRTUAL_ENV']}
ENV.update(PYTHONIOENCODING='utf-8',PYTHONNOUSERSITE='1',YOLO_AUTOINSTALL='false',YOLO_OFFLINE='true',YOLO_CONFIG_DIR=str(DATA/'ultralytics'))

def run(args,log=None):
    proc=subprocess.Popen([str(a) for a in args],cwd=ROOT,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
    for line in proc.stdout:
        print(line,end='',flush=True)
        if log: log.write(line);log.flush()
    code=proc.wait()
    if code: raise RuntimeError(f'İşlem tamamlanamadı (kod {code}).')

def verify_files():
    manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    for name,expected in manifest['sha256'].items():
        path=ROOT/name
        if not path.is_file() or hashlib.file_digest(path.open('rb'),'sha256').hexdigest()!=expected:
            raise ValueError('Paket dosyası eksik veya değişmiş: '+name)

def installed():
    try: stamp=json.loads((VENV/'glomquant_setup.json').read_text(encoding='utf-8'))
    except (OSError,ValueError): return False
    return PY.is_file() and stamp.get('package_path')==str(ROOT) and stamp.get('lock_sha256')==hashlib.sha256((ROOT/'requirements.lock.txt').read_bytes()).hexdigest()

def install():
    DATA.mkdir(parents=True,exist_ok=True)
    logpath=DATA/'kurulum.log'
    with logpath.open('w',encoding='utf-8') as log:
        print('Kurulum internetten sabit sürümlü bağımlılıkları indirecek. Mevcut Python kurulumları değiştirilmeyecek.')
        print('İlk kurulum birkaç dakika sürebilir. Kayıt: '+str(logpath))
        import venv
        venv.EnvBuilder(with_pip=True,clear=False,symlinks=False).create(VENV)
        run([PY,'-X','utf8','-E','-s','-m','pip','install','--disable-pip-version-check','--only-binary=:all:','--index-url','https://pypi.org/simple','-r',ROOT/'requirements.lock.txt'],log)
        run([PY,'-X','utf8','-E','-s','-m','pip','check'],log)
        run([PY,'-X','utf8','-E','-s',ROOT/'self_check.py'],log)
        (VENV/'glomquant_setup.json').write_text(json.dumps({'package_path':str(ROOT),'lock_sha256':hashlib.sha256((ROOT/'requirements.lock.txt').read_bytes()).hexdigest(),'status':'reference_gate_passed','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),encoding='utf-8')
    print('Kurulum ve örnek kontrolü tamamlandı. 3_BASLAT.cmd dosyasını açabilirsiniz.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['install','check','launch','integrity'])
    args=parser.parse_args()
    if sys.platform!='win32' or platform.machine().lower() not in ['amd64','x86_64']:
        raise RuntimeError('Bu paket Windows x64 içindir.')
    if sys.version_info[:2]!=(3,11):raise RuntimeError('Paketin Python 3.11 çalıştırıcısı kullanılmalı.')
    verify_files()
    if args.action=='integrity': print('Paket dosyalarının kimlik kontrolü başarılı.');return
    if args.action=='install':install();return
    if not installed():raise RuntimeError('Önce 1_KUR.cmd dosyasını çalıştırın. Kurulumdan sonra klasör taşındıysa kurulumu yeniden çalıştırın.')
    if args.action=='check':run([PY,'-X','utf8','-E','-s',ROOT/'self_check.py'])
    else:run([PY,'-X','utf8','-E','-s',ROOT/'app.py'])

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('\nİşlem tamamlanamadı: '+str(exc),file=sys.stderr)
        sys.exit(1)
