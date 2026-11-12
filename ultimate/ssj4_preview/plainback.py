"""Super Saiyan 4 Goku from behind (a preview; he is locked). The sheet drew a tail lying over his back (a red band, dark-light-light-mid-dark, from his waist up across his
back and over his sash). The owner: "It should just have his back not a tail on top of his back and then another tail at the bottom".
Paint his back plain: where BF Goku has his gi's back (orange) above the belt, his fur in BF's own shading; where BF has the belt,
the sash's blue; his hair, arms and legs as they are."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from frames import fr, GOKU, BF, R
GI_FUR={79:31, 63:32, 64:32, 65:104}
BELT={157:69, 159:158, 161:160}
FURS=(31,32,33,104,105); BLUES=(69,158,160)
def belt_rows(b):
    """BF's belt from behind: rows with a run of 5 or more navy pixels -> {row: (first, last)}"""
    out={}
    for y in range(54,66):
        run=best=None; s=None
        for x in range(30,80):
            if b[y,x] in BELT:
                s=x if s is None else s
                if best is None or x-s>best[1]-best[0]: best=(s,x)
            else: s=None
        if best and best[1]-best[0]>=4: out[y]=best
    # the belt is the top one or two of those rows (the rest are boots)
    ys=sorted(out)
    if not ys: return {}
    keep=[ys[0]]+([ys[1]] if len(ys)>1 and ys[1]==ys[0]+1 else [])
    return {y:out[y] for y in keep}
def plain_back(c, b):
    out=c.copy(); belt=belt_rows(b)
    if not belt: return out
    top=min(belt)
    for y in range(40,top):
        for x in range(30,80):
            if int(b[y,x]) in GI_FUR and int(c[y,x]) in FURS+BLUES: out[y,x]=GI_FUR[int(b[y,x])]
    for y,(x0,x1) in belt.items():
        for x in range(x0,x1+1):
            if int(c[y,x]) in FURS+BLUES: out[y,x]=BELT[int(b[y,x])]
    return out

# --- the preview: BFU_GOG_ROM=<debug build> python3 ultimate/ssj4_preview/plainback.py <out dir> ---
from PIL import Image, ImageDraw, ImageFont
SKINS = (200, 201, 202, 203, 16, 17)
def from_behind(c):
    """a frame that shows his back (BF draws some poses facing the camera in every view): no face in his head's rows"""
    ys = np.nonzero(c.any(1))[0]
    if not len(ys): return False
    head = c[ys.min():ys.min() + 16]
    return not np.isin(head, (110,)).any() and int(np.isin(head, SKINS).sum()) < 3
from frames import fr, GOKU, BF, R
NS={a:R.slots(a) for a in (GOKU,BF)}
_bf={}
def bf_for(k):
    s,f,d=k
    if NS[BF].get(s)==NS[GOKU].get(s): return fr(BF,*k)
    if k in _bf: return _bf[k]
    c=fr(GOKU,*k); cm=(c>0)&~np.isin(c,(1,111,112)); best=None
    for t,n in NS[BF].items():
        for g in range(n):
            b=fr(BF,t,g,d); bm=(b>0)&~np.isin(b,(1,111,112))
            if not bm.any(): continue
            for dy in range(-3,4):
                for dx in range(-4,5):
                    m=int((np.roll(np.roll(bm,dy,0),dx,1)&cm).sum())
                    if best is None or m>best[0]: best=(m,dy,dx,b)
    _bf[k]=np.roll(np.roll(best[3],best[1],0),best[2],1); return _bf[k]
def fixed(k):
    c=fr(GOKU,*k)
    return plain_back(c,bf_for(k)) if k[2]==1 and from_behind(c) else c
BG=(88,120,88); BOX=(37,72,39,80); H=BOX[1]-BOX[0]; W=BOX[3]-BOX[2]
F=ImageFont.load_default(size=16); FS=ImageFont.load_default(size=13)
def cell(c):
    c=c[BOX[0]:BOX[1],BOX[2]:BOX[3]]; rgb=R.rgb(c).copy(); rgb[c==0]=BG; return rgb
big=lambda im,z: Image.fromarray(im).resize((im.shape[1]*z,im.shape[0]*z),Image.NEAREST)
def gif(path,seq,ms,z=8,reps=3):
    frames=[]; band=22
    for _ in range(reps):
        for s,f in seq:
            img=Image.new('RGB',(2*W*z,H*z+band),BG); dr=ImageDraw.Draw(img); dr.rectangle((0,0,2*W*z,band),fill=(30,40,30))
            dr.text((6,3),'now (in the game)',fill=(255,255,255),font=F); dr.text((W*z+6,3),'his back plain',fill=(255,255,255),font=F)
            img.paste(big(np.concatenate([cell(fr(GOKU,s,f,1)),cell(fixed((s,f,1)))],1),z),(0,band)); frames.append(img)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=ms,loop=0)
if __name__=='__main__':
  OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True)
  gif(OUT+'/ssj4_goku_back_plain_walk.gif',[(1,f) for f in range(4)],170)
  gif(OUT+'/ssj4_goku_back_plain_run.gif',[(2,f) for f in range(4)],120)
  # a still: standing, walk, run from behind, now above plain, big
  keys=[(0,0,1)]+[(1,f,1) for f in range(4)]+[(2,f,1) for f in range(4)]; z=6; band=22
  img=Image.new('RGB',(9*W*z,2*(H*z+band)),BG); dr=ImageDraw.Draw(img); y=0
  for what,fn in (('now (in the game)',lambda k: fr(GOKU,*k)),('his back plain',fixed)):
      dr.rectangle((0,y,9*W*z,y+band),fill=(30,40,30)); dr.text((6,y+3),'from behind, standing, walk 1-4, run 1-4: '+what,fill=(255,255,255),font=F); y+=band
      img.paste(big(np.concatenate([cell(fn(k)) for k in keys],1),z),(0,y)); y+=H*z
  img.save(OUT+'/ssj4_goku_back_plain_now_and_fixed.png')
  # every frame from behind (each picture once), now above plain
  seen=set(); keep=[]
  for s in sorted(NS[GOKU]):
      if s>=22: continue
      for f in range(NS[GOKU][s]):
          c=fr(GOKU,s,f,1)
          if not c.any() or c.tobytes() in seen: continue
          seen.add(c.tobytes()); keep.append((s,f,1))
  per=10; rows=[]; changed=0
  for i in range(0,len(keep),per):
      chunk=keep[i:i+per]
      for fn in (lambda k: fr(GOKU,*k), fixed):
          cells=[cell(fn(k)) for k in chunk]+[np.full((H,W,3),BG,np.uint8)]*(per-len(chunk))
          rows.append(np.concatenate(cells,1))
      rows.append(np.full((3,per*W,3),255,np.uint8))
  changed=sum(int((fixed(k)!=fr(GOKU,*k)).any()) for k in keep)
  big(np.concatenate(rows,0),3).save(OUT+'/ssj4_goku_back_plain_every_frame.png')
  print(len(keep),'pictures from behind,',changed,'changed')
