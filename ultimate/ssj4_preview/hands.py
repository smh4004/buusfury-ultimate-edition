"""Scratch: where the sheet drew Super Saiyan 4 Goku's hands as fur, found on BF Goku's frames (gt.bf_hands), over every slot and view."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0,'ultimate')
from v2 import *
import gt
BF=106
def lay(b, c):
    """(dy, dx, overlap) laying BF's frame on the sheet's by the most overlap of everything but hair"""
    bm=(b>0)&(b!=1); cm=(c>0)&~np.isin(c,(1,111,112)); best=(-1,0,0)
    for dy in range(-4,5):
        for dx in range(-6,7):
            n=(np.roll(np.roll(bm,dy,0),dx,1)&cm).sum()
            if n>best[0]: best=(int(n),dy,dx)
    return best
_bf={}
def bf_frames(slot, d):
    if (slot,d) not in _bf:
        n=R.slots(BF).get(slot,0); _bf[slot,d]=[R.frame(BF,slot,f,d) for f in range(n)]
    return _bf[slot,d]
def hands(c, slot, d, most=28):
    """-> (the frame with hands of skin, pixels changed, which BF frame)"""
    best=None
    for k,b in enumerate(bf_frames(slot,d)):
        if not b.any(): continue
        n,dy,dx=lay(b,c)
        if best is None or n>best[0]: best=(n,dy,dx,k,b)
    if best is None: return c,0,None
    n,dy,dx,k,b=best; bb=np.roll(np.roll(b,dy,0),dx,1)
    fur=(bb>0)&np.isin(c,list(gt.SS4_FUR))
    why=[]; hand,wrist=gt.bf_hands(bb,fur,why,most)
    out=c.copy(); ch=0
    for y,x in np.argwhere(hand|wrist):
        if c[y,x] not in gt.SS4_FUR: continue
        new=bb[y,x] if hand[y,x] else gt.BF_BAND.get(int(bb[y,x]),c[y,x])
        if new!=c[y,x]: out[y,x]=new; ch+=1
    return out,ch,(k,dy,dx,why)
