"""Scratch: his arms are fur and his hands are skin, in every frame (the owner, Nov 11 19:29: "make sure the fur is always on his full
arms in every frame and only his hands without it, make sure hands never have the red fur on them"; 19:33: "Don't take fur off the tail
either"). The sheet was drawn on BF Goku's frames, and BF Goku's own frame says which is which: a hand is skin that touches one small
patch of blue only (its wristband); an arm touches two (its sleeve and its band). That is used only where the sheet's frame has the
same wristband in the same place (blue, or black as in his side stance): where the sheet posed the arm its own way, or his tail lies
there, nothing is touched.
  clean(c, slot, d, loc) -> (frame, [what was changed])
  bands(c) -> the frame's wristbands as the sheet has them; audit lists every band with no hand of skin beside it."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0,'ultimate')
import numpy as np
from scipy import ndimage
import gt
FURS=(31,32,33,105,104); BLUES=(69,157,158,159,160,161); DARKS=(1,111,112); SKINS=(200,201,202,203,16,17); TROUSERS=(24,25,26,27,28)
BOOT_DARK=(1,111,112,116,117,118,206)
TO_FUR={16:31, 17:31, 202:32, 203:32, 201:33, 200:105}
K8=np.ones((3,3))
def _shift(m, dy, dx): return np.roll(np.roll(m, dy, 0), dx, 1)
def clean(c, b, top, reach=4):
    """c: his frame; b: BF Goku's frame laid on it; top: the row his head starts at. Limb by limb. BF's wristband is found in the sheet's
    frame (the sheet moved some arms a pixel or a few): the sheet has no sleeves, so a small patch of its blue where BF has one is a
    wristband (two pixels of blue are enough; or the band drawn black, when that black is not his hair). Then BF's hand beyond it
    (skin touching that band only) must be skin, and BF's arm on its other side fur."""
    skin=np.isin(b,list(gt.BF_SKIN)); blue=np.isin(b,list(gt.BF_BAND))
    lab,n=ndimage.label(skin); blab,bn=ndimage.label(blue,K8)
    face=set(np.unique(lab[top:top+15]).tolist())-{0}; out=c.copy(); log=[]
    touch={t:set(np.unique(blab[ndimage.binary_dilation(lab==t,K8)&blue]).tolist())-{0} for t in range(1,n+1) if t not in face}
    cblue=np.isin(c,BLUES); cfur=np.isin(c,FURS)
    dlab,dn=ndimage.label(np.isin(c,DARKS),K8); hair=np.isin(dlab,list(set(np.unique(dlab[top:top+12]).tolist())-{0}))
    cdark=np.isin(c,DARKS)&~hair
    for k in range(1,bn+1):
        w=blab==k
        if w.sum()>16: continue
        hands=[t for t,ks in touch.items() if ks=={k} and 4<=(lab==t).sum()<=30]
        if not hands: continue
        best=None
        for dy in range(-reach,reach+1):
            for dx in range(-reach,reach+1):
                ws=_shift(w,dy,dx); nb=int((ws&cblue).sum()); nd=int((ws&cdark).sum())
                if nb>=2 or nd*2>=w.sum():
                    sc=2*nb+nd-0.1*(abs(dy)+abs(dx))
                    if best is None or sc>best[0]: best=(sc,dy,dx)
        if best is None: continue                                         # the sheet has no band here: its own pose, or out of sight
        _,dy,dx=best; ws=_shift(w,dy,dx); bsrc=_shift(b,dy,dx); fixed=False
        for t in hands:
            hs=_shift(lab==t,dy,dx)&~ws
            if (hs&np.isin(c,SKINS)).sum()*2>=hs.sum(): continue          # a hand of skin already
            fix=hs&(cfur|cdark)
            if fix.sum()*2<hs.sum(): continue                             # not there in the sheet (out of sight, or cut by the frame's edge)
            for y,x in zip(*np.nonzero(fix)): out[y,x]=bsrc[y,x]
            log.append(('hand',int(fix.sum()),(dy,dx))); fixed=True
        if fixed:
            for t,ks in touch.items():
                m=_shift(lab==t,dy,dx)&~ws
                if k in ks and len(ks)>=2:
                    bare=m&np.isin(c,SKINS)
                    for y,x in zip(*np.nonzero(bare)): out[y,x]=TO_FUR[int(c[y,x])]
                    if bare.any(): log.append(('arm',int(bare.sum())))
            band=ws&(cdark|cfur)
            for y,x in zip(*np.nonzero(band)): out[y,x]=gt.BF_BAND[int(bsrc[y,x])]
            if band.any(): log.append(('band',int(band.sum())))
    return out,log
TO_SKIN={31:16, 32:202, 33:201, 105:200, 104:201}
def fists(c, b):
    """A fist the sheet drew as a ball of fur at the end of a wristband of its own blue (his jump, his punches): the band has no hand of
    skin, and fur on two sides: his arm (the large patch, joined to his body's fur) and a small patch, which is the fist, where BF
    Goku has skin too (so never his tail: BF Goku has none). -> (frame, [pixels])"""
    out=c.copy(); log=[]; fur=np.isin(c,FURS); flab,fn=ndimage.label(fur); sizes=ndimage.sum(fur,flab,range(1,fn+1))
    bskin=np.isin(b,list(gt.BF_SKIN)); done=set()
    for w,bright,anyskin in bands(c):
        if bright>=2: continue
        ring=ndimage.binary_dilation(w,K8)&~w
        near=set(np.unique(flab[ring&fur]).tolist())-{0}
        if len(near)<2 or max(sizes[t-1] for t in near)<=30: continue
        for t in near:
            m=flab==t
            if t in done or not 4<=sizes[t-1]<=20 or (m&bskin).sum()*10<m.sum()*6: continue
            for y,x in zip(*np.nonzero(m)): out[y,x]=b[y,x] if int(b[y,x]) in gt.BF_SKIN else TO_SKIN[int(c[y,x])]
            log.append(('fist',int(m.sum()))); done.add(t)
    return out,log
# What the rules above cannot tell from the two frames alone, read off them side by side, frame by frame (Nov 11: every distinct frame's
# letter map, BF Goku's beside the new one, with BF's own structure as the guide: sleeve, arm, wristband, hand). Rectangles of the
# canvas: (first row, last row, first column, last column).
# FISTS: a hand the sheet drew as fur: BF's skin there.
FISTS={(7,0,2):((60,63,50,53),), (14,2,0):((58,61,48,51),(57,59,60,63)), (21,5,0):((57,60,49,53),(57,60,59,62)), (4,3,2):((59,62,42,45),),
       (2,0,2):((58,60,49,53),), (3,0,1):((61,61,59,60),(61,61,49,50)), (3,1,0):((56,60,46,50),), (3,1,1):((59,62,48,52),),
       (3,1,2):((60,60,61,63),), (3,2,0):((56,60,62,67),), (3,2,1):((60,63,58,62),), (4,1,1):((59,62,47,51),), (4,3,1):((58,59,49,51),),
       (5,1,1):((59,62,60,64),), (6,1,1):((58,58,48,49),(59,59,47,48),(60,61,47,47)), (6,2,1):((60,60,47,48),(61,61,46,47),(62,63,46,46)),
       (6,3,2):((58,61,55,58),), (7,0,0):((60,61,59,60),), (9,0,2):((56,59,52,56),), (14,0,0):((62,64,51,54),),
       (15,0,0):((63,64,59,60),), (15,1,0):((63,64,59,60),), (15,2,0):((63,64,59,60),),
       (16,0,0):((67,68,57,58),), (16,1,0):((67,68,57,58),), (16,2,0):((67,68,57,58),),
       (16,0,2):((67,68,53,54),), (16,1,2):((67,68,53,54),), (16,2,2):((67,68,53,54),),
       (17,0,0):((62,66,56,60),), (17,2,0):((69,70,33,33),), (17,3,0):((69,70,33,33),),
       (18,0,1):((58,61,62,64),(62,62,61,63),(63,63,59,62))}
# (the special's frames 4 and 5 are the change's frames 6 and 7 again: a frame is touched up as its first place in the figure)
FISTS[(10,7,0)]=FISTS[(21,5,0)]
def listed(c, b, key, c0=None):
    """c0: the frame before the new hair went on: a fist the new, wider hair now lies over (raised beside his head) comes back whole."""
    out=c.copy(); n=0
    for y0,y1,x0,x1 in FISTS.get(key,()):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if int(b[y,x]) not in gt.BF_SKIN: continue
                if c[y,x] in FURS or (c0 is not None and c[y,x] in DARKS and c0[y,x] in FURS+SKINS): out[y,x]=b[y,x]; n+=1
    return out,([('fist, listed',n)] if n else [])
# ARMS: an arm the sheet left bare: the sheet's skin there turns to fur.
ARMS={(13,0,0):((60,62,60,63),), (21,4,0):((56,59,59,62),),
      (1,0,1):((58,59,48,49),), (2,1,1):((56,58,48,49),), (2,3,1):((56,58,48,49),), (3,0,1):((58,59,48,49),), (3,1,1):((58,58,50,50),),
      (4,1,1):((58,58,49,49),), (3,2,1):((57,59,57,60),), (5,1,1):((56,58,59,62),), (6,0,1):((58,63,54,59),), (6,1,1):((59,62,50,53),),
      (6,2,1):((63,64,48,51),), (14,2,2):((56,60,60,63),), (17,0,0):((58,60,57,60),), (17,2,0):((70,71,40,45),), (17,3,0):((69,71,41,45),)}
ARMS[(10,6,0)]=ARMS[(21,4,0)]
def listed_arms(c, key):
    out=c.copy(); n=0
    for y0,y1,x0,x1 in ARMS.get(key,()):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if int(c[y,x]) in TO_FUR: out[y,x]=TO_FUR[int(c[y,x])]; n+=1
    return out,([('arm, listed',n)] if n else [])
# BANDS: a wristband the sheet drew as fur (or black): BF's blue there. SLEEVES: BF's sleeve the sheet kept blue (he has none): fur.
BANDS={(2,0,2):((57,58,48,49),), (4,3,1):((58,59,52,52),), (6,1,1):((59,61,48,49),), (6,2,1):((61,62,47,48),), (7,0,0):((60,61,57,58),),
       (17,0,0):((62,62,59,60),)}
SLEEVES={(17,0,0):((57,57,56,61),), (17,3,0):((69,70,45,46),)}
BLUE_FUR={69:31, 158:32, 160:33, 157:31, 159:32, 161:33}
# PIXELS: the walk's third frame from the front: his left arm ends in fur with no hand at all (BF's arm is three rows longer): its
# last two rows become a wristband and a hand.
PIXELS={(1,2,0):((60,48,69),(60,49,158),(61,49,202),(61,50,16))}
def listed_rest(c, b, key):
    out=c.copy(); log=[]
    for y0,y1,x0,x1 in BANDS.get(key,()):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if int(b[y,x]) in gt.BF_BAND and (c[y,x] in FURS or c[y,x] in DARKS): out[y,x]=gt.BF_BAND[int(b[y,x])]; log.append('band')
    for y0,y1,x0,x1 in SLEEVES.get(key,()):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if int(c[y,x]) in BLUE_FUR: out[y,x]=BLUE_FUR[int(c[y,x])]; log.append('sleeve')
    for y,x,v in PIXELS.get(key,()): out[y,x]=v; log.append('pixel')
    return out,([('rest, listed',len(log))] if log else [])
def everything(c, b, loc, key, c0=None):
    """All of it, in order. -> (frame, log)"""
    if b is None or loc is None: return c,[]
    out,log=clean(c,b,loc[2]); out,l2=fists(out,b); out,l3=listed(out,b,key,c0); out,l4=listed_arms(out,key); out,l5=listed_rest(out,b,key)
    return out,log+l2+l3+l4+l5
def bands(c):
    """[(mask, pixels of bright skin beside it)]: the sheet's wristbands: small patches of its blue that are not his sash or in a boot"""
    blue=np.isin(c,BLUES); blab,bn=ndimage.label(blue,K8); out=[]
    for k in range(1,bn+1):
        w=blab==k
        if w.sum()>14 or w.sum()<2: continue
        ring=ndimage.binary_dilation(w,K8)&~w; r=c[ring]
        if np.isin(r,BOOT_DARK).sum()*3>ring.sum(): continue
        if np.isin(r,TROUSERS).sum()*5>=ring.sum()*2 and w.sum()>=6: continue        # his sash
        wide=ndimage.binary_dilation(w,K8,iterations=2)&~w
        out.append((w,int(np.isin(c[wide],(200,201,203)).sum()),int(np.isin(c[wide],SKINS).sum())))
    return out

