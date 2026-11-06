"""Downloads every map in <MOON_MAPS>/index.csv plus the 1437 AH maps (data/maps_1437.csv),
which moonsighting.com still hosts but no longer lists. Needs curl. Skips files already present."""
import csv,os,sys,subprocess,concurrent.futures as cf,time
from PIL import Image
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import MAPS as R, DATA
CJ=os.path.join(R,'.cookies')
rows=[x for x in csv.DictReader(open(R+'index.csv',encoding='utf-8-sig')) if x['file']]
rows+=[x for x in csv.DictReader(open(DATA/'maps_1437.csv',encoding='utf-8'))]
def ok(p):
    try: return Image.open(p).size==(994,513)
    except Exception: return False
def get(x):
    dst=R+x['file']
    if ok(dst): return 'have'
    os.makedirs(os.path.dirname(dst),exist_ok=True)
    for i in range(6):
        subprocess.run(['curl','-sS','-m','30','-c',CJ,'-b',CJ,'-o',dst,x['source_url']],capture_output=True)
        if ok(dst): return 'ok'
        time.sleep(2+i*2)
    return 'FAIL '+x['file']
with cf.ThreadPoolExecutor(4) as ex: res=list(ex.map(get,rows))
import collections; print(collections.Counter(r if not r.startswith('FAIL') else 'FAIL' for r in res)); print([r for r in res if r.startswith('FAIL')][:10])
