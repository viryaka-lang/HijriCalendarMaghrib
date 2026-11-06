from PIL import Image
import collections
from config import MAPS as R
POLY=[(35.9,-5.9),(35.25,-2.9),(35.1,-2.2),(34.8,-1.75),(32.1,-1.2),(31.4,-3.7),(30.6,-5.5),(29.6,-7.4),(28.9,-8.7),(27.67,-8.67),
      (26.0,-8.67),(25.99,-12.0),(23.45,-12.0),(21.33,-13.0),(21.33,-16.95),(23.7,-15.9),(26.1,-14.5),(27.9,-12.9),(28.8,-11.0),
      (30.4,-9.7),(32.3,-9.3),(33.6,-7.6),(34.8,-6.4),(35.8,-5.9)]
def inside(lat,lon):
    c=False; n=len(POLY)
    for i in range(n):
        y1,x1=POLY[i]; y2,x2=POLY[i-1]
        if (y1>lat)!=(y2>lat) and lon < (x2-x1)*(lat-y1)/(y2-y1)+x1: c=not c
    return c
PTS=[(la/4,lo/4) for la in range(21*4,36*4+1) for lo in range(-17*4,-1*4+1) if inside(la/4,lo/4)]
def cls(p):
    r,g,b=p
    if r<30 and 90<=g<=170 and b<30: return 'A'
    if r<30 and g>150 and b>150: return 'B'
    if 90<=r<=215 and 90<=g<=215 and 90<=b<=215 and max(r,g,b)-min(r,g,b)<=60: return 'C'
    if r>200 and g<60 and b<60: return 'D'
    if r<25 and g<25 and b<25: return 'N'
    return None
def zone(px,lat,lon):
    x,y=round(497+lon*83/30), round(254-lat*85.5/30); c=collections.Counter()
    for dx in range(-2,3):
        for dy in range(-2,3):
            k=cls(px[x+dx,y+dy])
            if k: c[k]+=1
    return c.most_common(1)[0][0] if c else None
def feats(path):
    px=Image.open(R+path).convert('RGB').load()
    out={}
    for name,sel in [('all',lambda la:True),('north',lambda la:la>=29.5),('south',lambda la:la<29.5)]:
        c=collections.Counter(zone(px,la,lo) for la,lo in PTS if sel(la)); c.pop(None,None); n=sum(c.values()) or 1
        out[name]={k:round(c[k]/n,3) for k in 'ABCDN'}
    return out
if __name__=='__main__':
    print(len(PTS), sum(1 for la,lo in PTS if la>=29.5))
