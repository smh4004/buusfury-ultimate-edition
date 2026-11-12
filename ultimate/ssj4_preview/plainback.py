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
    """BF's belt from behind -> {row: (first, last column)}: the top one or two rows with a run of 5 or more navy pixels, cut to his
    waist (the columns of BF's gi in the row above it), so the wristbands at his sides are never taken for it"""
    found = {}
    for y in range(54, 66):
        best = None; st = None
        for x in range(30, 80):
            if b[y, x] in BELT:
                st = x if st is None else st
                if best is None or x - st > best[1] - best[0]: best = (st, x)
            else: st = None
        if best and best[1] - best[0] >= 4: found[y] = best
    ys = sorted(found)
    if not ys: return {}
    keep = [ys[0]] + ([ys[1]] if len(ys) > 1 and ys[1] == ys[0] + 1 else [])
    gi = np.nonzero(np.isin(b[keep[0] - 1], list(GI_FUR)))[0]
    if not len(gi): return {}
    lo, hi = int(gi.min()), int(gi.max())
    return {y: (max(found[y][0], lo), min(found[y][1], hi)) for y in keep}


def see_through(c):
    """see-through pixels inside his figure boxed in by his hair or outline (3 or 4 of the pixels beside one are black or the hair's
    greys): the sheet's, in 61 of his pictures, mostly where his hair ends (the owner, Nov 12: "there's a transparent pixel on his back
    at the bottom of his hair in back view") -> [(row, column)]"""
    from scipy import ndimage
    lab, n = ndimage.label(c == 0); edge = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1])
    return [(int(y), int(x)) for y, x in np.argwhere((lab > 0) & ~np.isin(lab, list(edge)))
            if sum(int(c[y + dy, x + dx]) in (1, 111, 112) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))) >= 3]


def fill(c):
    out = c.copy()
    for y, x in see_through(c): out[y, x] = 1
    return out


def plain_back(c, b):
    """his back from behind plain: only where BF has his gi's back above the belt (his fur, in BF's shading) and BF's belt across his
    waist (the sash's blue), and only over the sheet's fur there; his arms, hands, wristbands, hair and legs untouched; the
    see-through pixel at the bottom of his hair filled (black, as the hair's outline round it)"""
    out = fill(c); belt = belt_rows(b)
    if not belt: return out
    top = min(belt)
    for y in range(40, top):
        for x in range(30, 80):
            if int(b[y, x]) in GI_FUR and int(c[y, x]) in FURS: out[y, x] = GI_FUR[int(b[y, x])]
    for y, (x0, x1) in belt.items():
        for x in range(x0, x1 + 1):
            if int(b[y, x]) in BELT and int(c[y, x]) in FURS: out[y, x] = BELT[int(b[y, x])]
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
    return plain_back(c,bf_for(k)) if k[2]==1 and from_behind(c) else fill(c)
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
  # every see-through pixel filled, in any view: his head and shoulders close, now above filled, on magenta so they show
  todo=[]; seen=set()
  for s in sorted(NS[GOKU]):
    for f in range(NS[GOKU][s]):
      for d in range(3):
        c=fr(GOKU,s,f,d)
        if not c.any() or c.tobytes() in seen: continue
        seen.add(c.tobytes())
        if see_through(c): todo.append((s,f,d))
  hb=(38,62,40,72); per=8; rows=[]
  def mag(c):
    c=c[hb[0]:hb[1],hb[2]:hb[3]]; rgb=R.rgb(c).copy(); rgb[c==0]=(255,0,255); return np.pad(rgb,((0,1),(0,1),(0,0)),constant_values=255)
  for i in range(0,len(todo),per):
    chunk=todo[i:i+per]
    for fn in (lambda k: fr(GOKU,*k), fixed):
      cells=[mag(fn(k)) for k in chunk]; cells+=[np.full_like(cells[0],255)]*(per-len(cells)); rows.append(np.concatenate(cells,1))
    rows.append(np.full((4,rows[-1].shape[1],3),40,np.uint8))
  big(np.concatenate(rows,0),4).save(OUT+'/ssj4_goku_see_through_pixels_filled.png')
  # what changed, checked: nothing on his arms, hands, wristbands or sleeves (BF's skin, or BF's navy off the belt), only the
  # see-through pixels and, from behind, his back and sash
  SK=(200,201,202,203,16,17); arm=0; total=0
  for s in sorted(NS[GOKU]):
    for f in range(NS[GOKU][s]):
      for d in range(3):
        k=(s,f,d); c=fr(GOKU,*k)
        if not c.any(): continue
        x=fixed(k); diff=np.argwhere(x!=c); total+=len(diff)
        if d==1 and from_behind(c):
          b=bf_for(k); belt=belt_rows(b); holes=set(see_through(c))
          arm+=sum(1 for y,xx in diff if (int(y),int(xx)) not in holes and (int(b[y,xx]) in SK or (int(b[y,xx]) in BELT and int(y) not in belt)))
  print(len(todo),'pictures with see-through pixels;',total,'pixels changed in all; on his arms:',arm)
