"""Scratch, second look: Super Saiyan 4 Goku with Super Saiyan 4 Gogeta's hair shape in black (the owner, Nov 11 18:36: "B shape is
fine"; "that Gogeta hair looks like shit and has invisible pixels too plus his body looks bad with the tail and hair"; "More overall
motion like SSJ3 goku"; fur "Tiny bit darker"; Daima "fur can be a TINY bit darker ... pants are too orange find a middle ground").
A frame is three layers: his body (the frame with the old hair taken off and what it hid filled in from the body round it), the new
hair (moved for the frame's motion), and his own face on top. No pixel inside the figure is left empty."""
import sys, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib4 import *
# a built ROM with him in it (actor ids as in the Nov 11 ROMs: Super Saiyan 4 Goku 356, Super Saiyan 4 Gogeta 357)
R=Rom(__import__('os').environ.get('BFU_SSJ4_ROM', 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba')); AID, GOG = 356, 357
HAIR=(1,111,112); G_HAIR=(62,31,32,104,33)
ROWS, FULL_ROWS = 15, 18
def stance_head(aid, v, rows, width=None):
    c=R.frame(aid,0,0,v); ys,xs=np.nonzero(c); t=c[ys.min():ys.min()+rows].copy(); x0=np.nonzero(c[ys.min():ys.min()+ROWS].any(0))[0].min()
    x1=np.nonzero(c[ys.min():ys.min()+ROWS].any(0))[0].max()+1 if width is None else x0+width
    return t[:, x0:x1]
TPL={v:stance_head(AID,v,ROWS) for v in (0,1,2)}
FULL={v:stance_head(AID,v,FULL_ROWS,TPL[v].shape[1]) for v in (0,1,2)}
FACE_BOX={0:(11,14,8,15), 1:None, 2:None}
def old_hair(v):
    t=FULL[v]; cand=np.isin(t,HAIR)
    if FACE_BOX[v]:
        y0,y1,x0,x1=FACE_BOX[v]; cand[y0:y1,x0:x1]=False
    if v==0: cand[ROWS:]=False
    m=cand.copy(); m[ROWS:]=False
    while True:
        n=m.copy(); n[1:]|=m[:-1]; n&=cand; n|=m
        if (n==m).all(): return m
        m=n
OLD={v:old_hair(v) for v in (0,1,2)}
def find(img, t):
    H,W=img.shape; th,tw=t.shape; ink=np.argwhere(t>0); P=np.zeros((H+2*th,W+2*tw),np.uint8); P[th:th+H,tw:tw+W]=img
    acc=np.zeros((H+th,W+tw),np.int32)
    for y,x in ink: acc+=P[y:y+H+th,x:x+W+tw]==t[y,x]
    j=np.unravel_index(acc.argmax(),acc.shape); return acc[j]/len(ink), j[1]-tw, j[0]-th
_loc={}
def locate(img):
    k=img.tobytes()
    if k not in _loc:
        best=max((find(img,TPL[v])+(v,) for v in (0,1,2)), key=lambda r:r[0]); _loc[k]=best if best[0]>=0.9 else None
    return _loc[k]
# Gogeta's hair per view, in black: its outline and darkest red black, its reds two dark greys (calm: a black head of hair with a
# little light in its strands, as Goku's own). Sideways and from behind it ends at his shoulders, so his back and tail show.
G_ROWS={0:16,1:15,2:17}; G_OFF={0:(-2,0),1:(-1,0),2:(0,0)}; G_MAP=((1,1),(62,1),(31,111),(32,111),(104,112),(33,112))
def gogeta_hair(v):
    c=R.frame(GOG,0,0,v); ys,xs=np.nonzero(c); g=c[ys.min():ys.min()+G_ROWS[v]].copy(); x0=np.nonzero(g.any(0))[0].min(); g=g[:,x0:]
    red=np.isin(g,G_HAIR); near=red.copy()
    for dy in (-1,0,1):
        for dx in (-1,0,1): near|=np.roll(np.roll(red,dy,0),dx,1)
    m=red|((g==1)&near)
    if v==2: m[15:,:14]=False
    out=np.zeros_like(g)
    for k,to in G_MAP: out[m&(g==k)]=to
    return out
NEW={v:gogeta_hair(v) for v in (0,1,2)}
PIVOT={2:(9,12)}                                           # sideways: where the mane hangs from (row, column of the new hair's picture)
def rotated(h, deg):
    """The mane (all the hair behind the pivot) swung up and back by `deg` degrees about the pivot; the hair before it stays."""
    if not deg: return h
    py,px=PIVOT[2]; H,W=h.shape; M=6; out=np.zeros((H+2*M,W+2*M),h.dtype); a=math.radians(deg); ca,sa=math.cos(a),math.sin(a)
    out[M:M+H,M:M+px]=h[:,:px]
    for Y in range(H+2*M):
        for X in range(px+M,W+2*M):
            dy,dx=Y-M-py,X-M-px                           # screen: y down. Swinging up and back: the picture turns anticlockwise
            sx=ca*dx-sa*dy; sy=sa*dx+ca*dy
            y,x=int(round(py+sy)),int(round(px+sx))
            if 0<=y<H and px<=x<W and h[y,x]: out[Y,X]=h[y,x]
    return out, M
def swayed(h, s):
    """Front and back: the hair below his eyes swings `s` pixels to one side by its tips, less higher up."""
    if not s: return h
    H,W=h.shape; M=3; out=np.zeros((H,W+2*M),h.dtype)
    for y in range(H):
        d=int(round(s*max(0,y-7)/4.0)); out[y,M+d:M+d+W]=np.where(out[y,M+d:M+d+W]==0,h[y],out[y,M+d:M+d+W])
    return out, M
def enclosed(c):
    H,W=c.shape; seen=np.zeros((H,W),bool); q=[(y,x) for y in range(H) for x in (0,W-1) if c[y,x]==0]+[(y,x) for x in range(W) for y in (0,H-1) if c[y,x]==0]
    for p in q: seen[p]=True
    while q:
        y,x=q.pop()
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            Y,X=y+dy,x+dx
            if 0<=Y<H and 0<=X<W and c[Y,X]==0 and not seen[Y,X]: seen[Y,X]=True; q.append((Y,X))
    return (c==0)&~seen
NB=((-1,0),(1,0),(0,-1),(0,1))
def body_layer(img, y, x, v):
    """The frame without his old hair; what the hair hid of his body is filled from the body next to it (his neck and back are fur)."""
    out=img.copy(); H,W=img.shape; t=FULL[v]; gone=np.zeros((H,W),bool)
    for yy,xx in zip(*np.nonzero(OLD[v])):
        Y,X=y+yy,x+xx
        if 0<=Y<H and 0<=X<W and img[Y,X]==t[yy,xx]: out[Y,X]=0; gone[Y,X]=True
    return out, gone
def fill(out, gone, hair_now, y, leave=None):
    """Empty pixels the old hair covered: body where body is on two sides (or it is shut in below the head), else left to the air.
    leave: gaps the frame had before (between his arm and his side): they stay gaps."""
    H,W=out.shape
    for _ in range(6):
        shut=enclosed(out); todo=[]
        if leave is not None: shut&=~leave
        for Y,X in zip(*np.nonzero((gone|shut)&(out==0))):
            nb=[out[Y+a,X+b] for a,b in NB if 0<=Y+a<H and 0<=X+b<W]
            body=[c for c in nb if c and c not in (1,111,112)]
            hair=[c for c in nb if c in (1,111,112)]
            if shut[Y,X]: todo.append((Y,X,max(set(body),key=body.count) if len(body)>=2 and Y>=y+12 else 1 if hair else (body[0] if body else 0)))
            elif len(body)>=2 and Y>=y+11: todo.append((Y,X,max(set(body),key=body.count)))
        todo=[t for t in todo if t[2]]
        if not todo: break
        for Y,X,c in todo: out[Y,X]=c
    return out
FUR={105:104, 33:104}                                      # his fur's two lights down to the next red
DAIMA={31:32, 32:129, 33:129, 105:121, 104:129, 24:80, 25:64, 26:109, 27:110}
DAIMA_HAIR={1:104, 111:129, 112:121}
MOTION={1:([4,0,6,0],[1,0,-1,0]), 2:([12,4,24,8],[1,0,-1,0]), 3:([0,10,18],[0,0,0]), 4:([0,8,16,6],[0,1,0,-1]), 5:([0,8,16,6],[0,-1,0,1]),
        6:([0,10,18,8],[0,1,0,-1]), 18:([6,14,22,16,22,16],[0,0,0,0,0,0])}
def shaped(slot, f, d, views=(0,1,2), motion=True):
    """The frame with Gogeta's hair shape where its head is one of `views` (0 front, 1 back, 2 side), in his own colours.
    -> (frame, where its head was found or None)"""
    img=R.frame(AID,slot,f,d); loc=locate(img); out=img.copy()
    if loc is not None and loc[3] in views:
        sc,x,y,v=loc; out,gone=body_layer(img,y,x,v); h=NEW[v]; dx,dy=G_OFF[v]; M=0
        if motion and slot in MOTION:
            deg,sw=MOTION[slot]
            if v==2 and deg[f%len(deg)]: h,M=rotated(h,deg[f%len(deg)])
            elif v!=2 and sw[f%len(sw)]: h,M=swayed(h,sw[f%len(sw)])
        H,W=img.shape; t=FULL[v]; face=(t>0)&~OLD[v]; face[ROWS:]=False
        my=M if (v==2 and M) else 0
        for yy,xx in zip(*np.nonzero(h)):
            Y,X=y+dy+yy-my,x+dx+xx-M
            if not (0<=Y<H and 0<=X<W): continue
            ty,tx=Y-y,X-x
            if 0<=ty<t.shape[0] and 0<=tx<t.shape[1] and face[ty,tx]: continue
            out[Y,X]=h[yy,xx]
        out=fill(out,gone,None,y,leave=enclosed(img))
    return out, loc
def frame(slot, f, d, kind, motion=True):
    """kind: 'now', 'new' (Gogeta's hair shape, the fur darker), 'daima' (the new look in Daima's colours), 'daima_old' (Daima's colours on
    the hair he has now)."""
    img=R.frame(AID,slot,f,d)
    if kind=='now': return img
    loc=locate(img); out=img.copy()
    if loc is not None and kind!='daima_old':
        sc,x,y,v=loc; out,gone=body_layer(img,y,x,v); h=NEW[v]; dx,dy=G_OFF[v]; M=0
        if motion and slot in MOTION:
            deg,sw=MOTION[slot]
            if v==2 and deg[f%len(deg)]: h,M=rotated(h,deg[f%len(deg)])
            elif v!=2 and sw[f%len(sw)]: h,M=swayed(h,sw[f%len(sw)]); dy0=0
            if v!=2 and M: h=np.pad(h,((0,0),(0,0)))
        H,W=img.shape; t=FULL[v]; face=(t>0)&~OLD[v]; face[ROWS:]=False
        my=M if (v==2 and M) else 0
        for yy,xx in zip(*np.nonzero(h)):
            Y,X=y+dy+yy-my,x+dx+xx-M
            if not (0<=Y<H and 0<=X<W): continue
            ty,tx=Y-y,X-x
            if 0<=ty<t.shape[0] and 0<=tx<t.shape[1] and face[ty,tx]: continue
            out[Y,X]=h[yy,xx]
        out=fill(out,gone,None,y)
    res=out.copy()
    for k,to in (FUR if kind=='new' else DAIMA).items(): res[out==k]=to
    if kind.startswith('daima') and loc is not None:
        sc,x,y,v=loc; H,W=img.shape
        hairpx=np.isin(out,(1,111,112)); keep=np.zeros((H,W),bool); t=FULL[v]; face=(t>0)&~OLD[v]; face[ROWS:]=False
        for yy,xx in zip(*np.nonzero(face)):
            if 0<=y+yy<H and 0<=x+xx<W: keep[y+yy,x+xx]=True
        zone=np.zeros((H,W),bool); zone[max(y-8,0):y+19]=True     # his head and what hangs from it
        # hair: black and grey joined to the top of his head, outside his face
        m=hairpx&zone&~keep; seed=np.zeros((H,W),bool); seed[max(y-8,0):y+6]=m[max(y-8,0):y+6]
        while True:
            n=seed.copy(); n[1:]|=seed[:-1]; n[:-1]|=seed[1:]; n[:,1:]|=seed[:,:-1]; n[:,:-1]|=seed[:,1:]; n&=m
            if (n==seed).all(): break
            seed=n
        for k,to in DAIMA_HAIR.items(): res[seed&(out==k)]=to
    return res
def extent(c):
    ys,xs=np.nonzero(c); return (xs.max()-xs.min()+1, ys.max()-ys.min()+1) if len(ys) else (0,0)
