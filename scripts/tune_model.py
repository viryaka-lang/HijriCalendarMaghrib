"""Walk-forward comparison of recency half-life and regularisation for the borderline model."""
import json,numpy as np,datetime as dt
from sklearn.linear_model import LogisticRegression
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from config import DATA
D=json.load(open(DATA/'dataset.json'))
lab=sorted([r for r in D['hist']+D['recent'] if r['seen'] is not None],key=lambda r:r['ev'])
X=np.array([[r['f']['all'][k] for k in 'ABC'] for r in lab]); y=np.array([r['seen'] for r in lab],float)
T=np.array([dt.date.fromisoformat(r['ev']).toordinal() for r in lab])
def gate(f): return 'A' if f['A']>0.02 else ('N' if f['A']+f['B']+f['C']<0.02 else 'M')
G=np.array([gate(r['f']['all']) for r in lab])
def p_at(i,HL,C):
    sel=T<T[i]; g=G[i]
    if g in 'AN': k=sel&(G==g); return (y[k].sum()+1)/(k.sum()+2)
    k=sel&(G=='M'); w=np.ones(k.sum()) if HL is None else 0.5**((T[i]-T[k])/(HL*365.25))
    if len(set(y[k]))<2: return (y[k].sum()+1)/(k.sum()+2)
    return LogisticRegression(C=C,max_iter=5000).fit(X[k][:,1:],y[k],sample_weight=w*k.sum()/w.sum()).predict_proba(X[i:i+1,1:])[0,1]
start=20
for HL in [None,6,4,3,2,1.5,1]:
  for C in [1,3]:
    p=np.array([p_at(i,HL,C) for i in range(start,len(y))]); yy=y[start:]; m=(G[start:]=='M')
    rec=T[start:]>=dt.date(2024,7,1).toordinal()
    print(f'HL={HL} C={C} all brier {np.mean((p-yy)**2):.4f} acc {np.mean((p>.5)==yy):.3f} | border n={m.sum()} brier {np.mean((p[m]-yy[m])**2):.3f} acc {np.mean((p[m]>.5)==yy[m]):.3f} | recent border brier {np.mean((p[m&rec]-yy[m&rec])**2):.3f}')
print('n',len(y),'M',(G=='M').sum(),'A',(G=='A').sum(),'N',(G=='N').sum(), 'A seen',y[G=='A'].sum(),'N seen',y[G=='N'].sum())
