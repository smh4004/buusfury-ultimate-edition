"""One frame as three letter maps side by side: BF Goku's, Super Saiyan 4 Goku's, Super Saiyan 4 Gogeta's (one canvas, nothing shifted).
  python3 ultimate/gogeta_preview/three.py <slot> <frame> <view> [BF slot] [BF frame]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview'), os.path.join(HERE, '..')]
import numpy as np
from frames import fr, GOG, GOKU, BF, NS, R
# one alphabet for the three: S skin, n navy (BF) / blue band (Goku), o BF gi orange, F Goku fur, P plum fur, O pad orange, B sash blue, g vest grey, w white, h hair, # black
def L(v, who):
    if v==0: return '.'
    if v==1: return '#'
    if v in (200,201,202,203,16,17,205,206,207): return 'S'
    if who=='bf':
        if v in (157,159,161): return 'n'
        if v in (63,64,65,79,78): return 'o'
        if v in (111,112): return 'h'
        return '?'
    if who=='goku':
        if v in (31,32,33,104,105): return 'F'
        if v in (69,158,160): return 'n'
        if v in (111,112): return 'h'
        if v in (24,25,26,27,28): return 'y'
        if v==110: return 'e'
        return '?'
    if v==62: return 'x'
    if v in (31,32,104,33): return 'h'
    if v in (127,129): return 'P'
    if v in (64,109): return 'O'
    if v in (175,176,158): return 'B'
    if v in (111,112): return 'g'
    if v in (116,117,118,120,2): return 'w'
    if v in (77,78): return 'b'
    return '?'
def show(s,f,d,bs=None,bfk=None,rows=None,cols=None):
    g=fr(GOG,s,f,d); b=fr(BF,bs if bs is not None else s,bfk if bfk is not None else f,d); k=fr(GOKU,s,f,d)
    allm=(g>0)|(b>0)|(k>0); ys,xs=np.nonzero(allm)
    r0,r1=rows or (ys.min(),ys.max()); c0,c1=cols or (xs.min(),xs.max())
    print('slot %d frame %d view %d   BF Goku | approved SSJ4 Goku | SS4 Gogeta   (cols %d..%d)'%(s,f,d,c0,c1))
    for r in range(r0,r1+1):
        print('%2d '%r+'  '.join(''.join(L(int(c[r,x]),w) for x in range(c0,c1+1)) for c,w in ((b,'bf'),(k,'goku'),(g,'gog'))))
if __name__=='__main__':
    a=[int(x) for x in sys.argv[1:]]; show(*a[:3],*(a[3:5] if len(a)>3 else ()))
