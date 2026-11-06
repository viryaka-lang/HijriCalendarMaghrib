"""Builds data/calendar.json and index.html: walk-forward predictions for every past month,
forecasts to 1460 AH, and the page itself (scripts/template.html with the data inlined).
Usage: MOON_MAPS=/path/to/maps python scripts/build_calendar.py   (TODAY=YYYY-MM-DD optional)"""
import json,csv,datetime as dt,base64,io,sys,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from features import feats
from PIL import Image,ImageDraw
from sklearn.linear_model import LogisticRegression
from config import MAPS as R, DATA, ROOT
TODAY=os.environ.get('TODAY',dt.date.today().isoformat())
idx=list(csv.DictReader(open(R+'index.csv',encoding='utf-8-sig')))
D=json.load(open(DATA/'dataset.json'))
lab=sorted([r for r in D['hist']+D['recent'] if r['seen'] is not None],key=lambda r:r['ev'])
X=np.array([[r['f']['all'][k] for k in 'ABC'] for r in lab]); y=np.array([r['seen'] for r in lab],float)
T=np.array([dt.date.fromisoformat(r['ev']).toordinal() for r in lab])
HL,C=2.0,3
def gate(f):
    if f['A']>0.02: return 'A'
    if f['A']+f['B']+f['C']<0.02: return 'N'
    return 'M'
G=np.array([gate(r['f']['all']) for r in lab])
class Model:
    def __init__(s,upto_ord):
        sel=T<upto_ord; s.n=int(sel.sum())
        s.rate={}
        for g in 'AN':
            k=sel&(G==g); s.rate[g]=((y[k].sum()+1)/(k.sum()+2), int(y[k].sum()), int(k.sum()))
        k=sel&(G=='M'); w=0.5**((upto_ord-T[k])/(HL*365.25))
        s.lr=LogisticRegression(C=C,max_iter=5000).fit(X[k][:,1:],y[k],sample_weight=w*k.sum()/w.sum()); s.nm=int(k.sum())
    def p(s,f):
        g=gate(f)
        if g in 'AN': return float(s.rate[g][0])
        return float(s.lr.predict_proba([[f['B'],f['C']]])[0,1])
def model(upto_ord): return Model(upto_ord)
def prob(m,f): return m.p(f)
D_=dt.date.fromisoformat
# ---- history: walk-forward for every labelled evening (need >=20 earlier)
histout=[]
for i,r in enumerate(lab):
    p=None
    if i>=20: p=prob(model(T[i]),r['f']['all'])
    a=r['f']['all']
    histout.append(dict(ev=r['ev'],hy=r['hy'],hm=r['hm'],seen=bool(r['seen']),p=None if p is None else round(p,4),
        naive=1.0 if a['A']>0.02 else 0.0, border=a['A']<0.02 and a['B']+a['C']>0.3, f={k:a[k] for k in 'ABCDN'}))
def stats(sel):
    h=[x for x in histout if x['p'] is not None and sel(x)]
    yy=np.array([x['seen'] for x in h],float); p=np.array([x['p'] for x in h]); nv=np.array([x['naive'] for x in h])
    return dict(n=len(h),acc=round(float(np.mean((p>.5)==yy)),3),brier=round(float(np.mean((p-yy)**2)),3),
                nacc=round(float(np.mean((nv>.5)==yy)),3),nbrier=round(float(np.mean((nv-yy)**2)),3))
ST=dict(all=stats(lambda x:True),border=stats(lambda x:x['border']),recent=stats(lambda x:x['ev']>='2024-07-06'),
        recent_border=stats(lambda x:x['ev']>='2024-07-06' and x['border']))
today=D_(TODAY).toordinal()
final=model(today+1)
coef=dict(B=round(float(final.lr.coef_[0][0]),2),C=round(float(final.lr.coef_[0][1]),2),b=round(float(final.lr.intercept_[0]),2),rateA=final.rate['A'],rateN=final.rate['N'],nM=final.nm,n=final.n)
print(ST); print(coef)
# ---- months & evidence
names=['Muharram','Safar','Rabi al-Awwal','Rabi al-Thani','Jumada al-Ula','Jumada al-Thani','Rajab','Shaban','Ramadan','Shawwal','Dhul-Qadah','Dhul-Hijjah']
MS='https://www.moonsighting.org.uk/moon/sighting-reports/report-%d-%02d.html'
starts=[(1444,12,'2023-06-20','https://www.moonsighting.org.uk/moon/sighting-reports/report-1444-12.html'),(1445,1,'2023-07-19',MS%(1445,1)),(1445,2,'2023-08-18',MS%(1445,2)),(1445,3,'2023-09-17',MS%(1445,3)),(1445,4,'2023-10-17',MS%(1445,4)),(1445,5,'2023-11-15',MS%(1445,5)),(1445,6,'2023-12-15',MS%(1445,6)),(1445,7,'2024-01-13',MS%(1445,7)),(1445,8,'2024-02-11',MS%(1445,8)),(1445,9,'2024-03-12',MS%(1445,9)),(1445,10,'2024-04-10',MS%(1445,10)),(1445,11,'2024-05-10',MS%(1445,11)),(1445,12,'2024-06-08',MS%(1445,12)),(1446,1,'2024-07-07',MS%(1446,1)),(1446,2,'2024-08-06',MS%(1446,2)),(1446,3,'2024-09-05',MS%(1446,3)),
        (1446,4,'2024-10-05',MS%(1446,4)),(1446,5,'2024-11-04',MS%(1446,5))]
old=json.load(open(DATA/'official_months_2024_2026.json'))
for m in old:
    if not m['pending'] or m['hm']==5: starts.append((m['hy'],m['hm'],m['start'],m['src']))
starts=sorted(set(starts))
def maps_for(hy,hm): return sorted([x for x in idx if int(x['hijri_year'])==hy and int(x['month_no'])==hm],key=lambda x:x['gregorian_date'])
def featd(hy,hm,date):
    for x in maps_for(hy,hm):
        if x['gregorian_date']==date: return feats(x['file']),int(x['evening'])
    first=maps_for(hy,hm)[0]['gregorian_date']
    if date<first: return dict(all=dict(A=0,B=0,C=0,D=0,N=1)),0
    return dict(all=dict(A=1,B=0,C=0,D=0,N=0)),4
POLYCITY=[(34.0,-6.8),(31.6,-8.0),(27.15,-13.2),(23.7,-15.9),(34.7,-1.9)]
def thumb(file):
    im=Image.open(R+file).convert('RGB')
    x0=round(497-19*83/30); y0=round(254-37.5*2.85); x1=round(497+1*83/30); y1=round(254-19.5*2.85)
    c=im.crop((x0,y0,x1,y1)); c=c.resize((c.width*3,c.height*3),Image.NEAREST); d=ImageDraw.Draw(c)
    for la,lo in POLYCITY:
        x=(497+lo*83/30-x0)*3; yy=(254-la*2.85-y0)*3; d.ellipse((x-4,yy-4,x+4,yy+4),fill=(255,255,255),outline=(0,0,0),width=2)
    c=c.convert('P',palette=Image.ADAPTIVE,colors=24); b=io.BytesIO(); c.save(b,'PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
labmap={(r['hy'],r['hm']):r for r in histout}
months=[]; evidence=[]
for (hy,hm,s,src),nxt in zip(starts,starts[1:]+[None]):
    months.append(dict(hy=hy,hm=hm,name=names[hm-1],start=s,src=src,status='official'))
for i in range(1,len(months)):
    m=months[i]; prev=months[i-1]
    ev=(D_(prev['start'])+dt.timedelta(28)).isoformat()
    f,evn=featd(m['hy'],m['hm'],ev)
    p=prob(model(D_(ev).toordinal()),f['all'])
    seen=(D_(m['start'])-D_(prev['start'])).days==29
    mp=[dict(date=x['gregorian_date'],ev=int(x['evening']),img=thumb(x['file'])) for x in maps_for(m['hy'],m['hm'])]
    evidence.append(dict(hy=m['hy'],hm=m['hm'],name=m['name'],ev=ev,evening=evn,f=f['all'],p=round(p,4),seen=seen,
        alt=[(D_(ev)+dt.timedelta(1)).isoformat(),(D_(ev)+dt.timedelta(2)).isoformat()],actual=m['start'],src=m['src'],maps=mp,status='official'))
months=months[1:]  # drop Dhul-Hijjah 1445 (anchor only)
# ---- future: forward pass (marginals) + Viterbi (most likely consistent path), Jumada al-Thani 1448 .. Muharram 1461
FC={}
def featc(hy,hm,date):
    k=(hy,hm,date)
    if k not in FC: FC[k]=featd(hy,hm,date)
    return FC[k]
seq=[(1448,m) for m in range(6,13)]+[(y,m) for y in range(1449,1461) for m in range(1,13)]+[(1461,1)]
last=months[-1]
dist={last['start']:1.0}; vit={last['start']:(1.0,None)}
steps=[]
for hy,hm in seq:
    nd={}; nv={}; branches=[]
    for s_,ps in dist.items():
        ev=(D_(s_)+dt.timedelta(28)).isoformat(); f,evn=featc(hy,hm,ev); p=prob(final,f['all'])
        if ps>=0.01: branches.append(dict(prev_start=s_,pprev=round(ps,4),ev=ev,evening=evn,f=f['all'],p=round(p,4)))
        for d_,q in [((D_(ev)+dt.timedelta(1)).isoformat(),p),((D_(ev)+dt.timedelta(2)).isoformat(),1-p)]:
            nd[d_]=nd.get(d_,0)+ps*q
    for s_,(vs,_) in vit.items():
        ev=(D_(s_)+dt.timedelta(28)).isoformat(); f,evn=featc(hy,hm,ev); p=prob(final,f['all'])
        for d_,q in [((D_(ev)+dt.timedelta(1)).isoformat(),p),((D_(ev)+dt.timedelta(2)).isoformat(),1-p)]:
            if q*vs>nv.get(d_,(0,None))[0]: nv[d_]=(q*vs,s_)
    tot=sum(nd.values()); dist={k:v/tot for k,v in sorted(nd.items()) if v/tot>0.002}
    vit={k:v for k,v in nv.items() if v[0]>1e-12}
    mx=max(v[0] for v in vit.values()); vit={k:(v[0]/mx,v[1]) for k,v in vit.items()}
    steps.append(dict(hy=hy,hm=hm,dist=dist,vit=vit,branches=branches))
# backtrack
path=[None]*len(steps); cur=max(steps[-1]['vit'],key=lambda k:steps[-1]['vit'][k][0])
for i in range(len(steps)-1,-1,-1):
    path[i]=cur; cur=steps[i]['vit'][cur][1]
fut=[]
for st,start in zip(steps,path):
    hy,hm=st['hy'],st['hm']
    dd_={k:round(v,4) for k,v in st['dist'].items() if v>=0.005}
    mp=[dict(date=x['gregorian_date'],ev=int(x['evening']),img=thumb(x['file'])) for x in maps_for(hy,hm)] if hy<=1460 else []
    fut.append(dict(hy=hy,hm=hm,name=names[hm-1],dist=dd_,best=start,branches=st['branches'],maps=mp,status='forecast'))
    months.append(dict(hy=hy,hm=hm,name=names[hm-1],start=start,src=None,status='forecast',dist=dd_))
for f in fut[:3]+fut[-3:]: print(f['hy'],f['hm'],f['best'],f['dist'])
for i,m in enumerate(months[:-1]): m['len']=(D_(months[i+1]['start'])-D_(m['start'])).days
months[-1]['len']=29
out=dict(months=months,evidence=evidence,future=fut,hist=histout,stats=ST,coef=coef,hl=HL,today=TODAY)
js=json.dumps(out,separators=(',',':'))
open(DATA/'calendar.json','w').write(js)
tpl=open(ROOT/'scripts'/'template.html',encoding='utf-8').read()
open(ROOT/'index.html','w',encoding='utf-8').write(tpl.replace('__DATA__',js))
print('wrote index.html and data/calendar.json')
import build_simple; open(ROOT/'calendar.html','w',encoding='utf-8').write(build_simple.render()); print('wrote calendar.html')
for e in evidence: print(e['hy'],e['hm'],e['ev'],e['evening'],'p=%.2f'%e['p'],'seen' if e['seen'] else 'not', 'OK' if (e['p']>.5)==e['seen'] else 'MISS')
