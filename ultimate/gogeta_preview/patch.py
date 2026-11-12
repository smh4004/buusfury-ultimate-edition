"""Text patches for Super Saiyan 4 Gogeta's frames (places on frames.py's canvas), an exact alphabet for his colours, and maps to read a
frame beside BF Goku's.
  python3 ultimate/gogeta_preview/patch.py <view> <row0> <row1> <col0> <col1> <slot>/<frame> ..."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview'), os.path.join(HERE, '..')]
import numpy as np
from frames import fr, GOG, GOKU, BF, NS, R
SKIN=(200,201,202,203,16,17,205,206,207)
ABC={'.':0,'#':1,'O':64,'o':109,'P':129,'p':127,'x':62,'g':111,'G':112,'B':175,'b':176,'n':158,'w':118,'W':120,'v':116,'V':117,'2':2,
     'S':200,'T':201,'t':202,'U':203,'d':16,'h':31,'H':32,'k':104,'K':33,'e':77,'E':78,'f':205,'F':206}
INV={v:k for k,v in ABC.items()}
def letters(c,r,c0,c1): return ''.join(INV.get(int(v),'?') for v in c[r,c0:c1+1])
def bfl(v):
    if v==0: return '.'
    if v in SKIN: return 'S'
    if v in (157,159,161): return 'n'
    if v in (63,64,65,79,78): return 'o'
    if v in (1,111,112): return '#'
    return '?'
def show(key,rows,cols,after=None,bf=None):
    g=fr(GOG,*key); s,f,d=key; b=fr(BF,*(bf or key))
    print('%s cols %d..%d   BF | Gogeta now%s'%(key,cols[0],cols[1],' | fixed' if after is not None else ''))
    for r in range(rows[0],rows[1]+1):
        t='%2d '%r+''.join(bfl(int(v)) for v in b[r,cols[0]:cols[1]+1])+'  '+letters(g,r,*cols)
        if after is not None: t+='  '+letters(after,r,*cols)+('  <' if (after[r]!=g[r]).any() else '')
        print(t)
PLUM={200:129,201:129,203:129,202:127,16:127,17:127,205:127,206:127,207:127}
BAND={157:1,159:111,161:112}
NAVY=(157,159,161)
def apply(c,b,rows):
    """rows: (row, col, 'letters') puts letters ('_' leaves a pixel, 's' is BF's own skin there);
    ('arm', (r0, r1, c0, c1)): BF's skin in the box becomes fur (what is fur already stays);  ('bare', box): the same, only where he is skin now;
    ('fist', box): BF's skin in the box is skin, in BF's own shades;  ('band', box): BF's navy in the box is the dark wristband"""
    out=c.copy()
    for e in rows:
        if isinstance(e[0],str):
            op,(r0,r1,c0,c1)=e
            for r in range(r0,r1+1):
                for x in range(c0,c1+1):
                    v=int(b[r,x])
                    if op=='arm' and v in SKIN and out[r,x] not in (127,129,62): out[r,x]=PLUM[v]
                    elif op=='bare' and v in SKIN and out[r,x] in SKIN: out[r,x]=PLUM[v]
                    elif op=='fist' and v in SKIN: out[r,x]=v
                    elif op=='band' and v in NAVY: out[r,x]=BAND[v]
            continue
        r,c0,t=e
        for i,ch in enumerate(t):
            if ch=='_': continue
            if ch=='s':
                v=int(b[r,c0+i]); out[r,c0+i]=v if v in SKIN else 202
            else: out[r,c0+i]=ABC[ch]
    return out
if __name__=='__main__':
    d=int(sys.argv[1]); rows=(int(sys.argv[2]),int(sys.argv[3])); cols=(int(sys.argv[4]),int(sys.argv[5]))
    for k in sys.argv[6:]:
        s,f=[int(x) for x in k.split('/')]; show((s,f,d),rows,cols)
