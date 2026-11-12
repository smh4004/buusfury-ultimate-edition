"""Super Saiyan 4 Goku's touch-up, as pictures for the owner (Nov 11): nothing here is in a build until he approves.
  python3 ultimate/ssj4_preview/preview.py OUTDIR      (reads a built ROM: BFU_SSJ4_ROM, or ultimate/out's debug ROM)
v4.frame(slot, frame, view, kind) is the figure: 'now', 'mix' (the GT form: Gogeta's front hair), 'daima', 'daima_pic'.
armhand.py holds the frame-by-frame reading of his hands and arms (see the README, Nov 11 evening)."""
import sys, os
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import v4
from v4 import *
from PIL import ImageDraw, ImageFont
out=sys.argv[1]; os.makedirs(out,exist_ok=True); F=ImageFont.load_default(size=18); FS=ImageFont.load_default(size=15)
BOX=(64-40,64+9,48-22,48+30); BG=(88,120,88)
_c={}
def fr(slot,f,d,kind):
    k=(slot,f,d,kind)
    if k not in _c: _c[k]=v4.frame(slot,f,d,kind)
    return _c[k]
def cell(c,flip=False):
    im=R.rgb(c[BOX[0]:BOX[1],BOX[2]:BOX[3]]); return im[:,::-1] if flip else im
def big(im,z): return Image.fromarray(im).resize((im.shape[1]*z,im.shape[0]*z),Image.NEAREST)
n=R.slots(AID); CH=BOX[1]-BOX[0]; CW=BOX[3]-BOX[2]
NAMES=(('now','as he is now'),('mix','new'),('daima_pic','Daima'))      # (the owner, Nov 11 20:53: "use B plum for daima")
Z=6; rows=[]; texts=[]
for k,(kind,name) in enumerate(NAMES):
    cells=[cell(fr(0,0,d,kind)) for d in (0,2,1)]+[cell(fr(18,3,0,kind)),cell(fr(13,1,0,kind)),cell(fr(2,1,2,kind))]
    rows.append(np.concatenate(cells,1)); texts.append((6,k*CH*Z+4,name))
img=big(np.concatenate(rows,0),Z); dr=ImageDraw.Draw(img)
for x,y,t in texts: dr.text((x,y),t,fill=(255,255,255),font=F)
img.save(out+'/ssj4_goku_fourth_look.png')
# the front hair beside Gogeta's
g=R.frame(v2.GOG,0,0,0); HB=(34,62,48-22,48+26)
hd=lambda c: R.rgb(c[HB[0]:HB[1],HB[2]:HB[3]])
row=np.concatenate([hd(g),hd(fr(0,0,0,'mix')),hd(fr(0,0,0,'now'))],1); img=big(row,10); dr=ImageDraw.Draw(img)
for i,t in enumerate(('Super Saiyan 4 Gogeta','Goku: new front hair','Goku: as he is now')): dr.text((i*(HB[3]-HB[2])*10+6,4),t,fill=(255,255,255),font=F)
img.save(out+'/ssj4_goku_front_hair_beside_gogeta.png')

# every frame where a hand, an arm or a wristband changed: as he is now beside new
SK=(200,201,202,203,16,17); FU=(31,32,33,105,104); BL=(69,158,160)
def cls(a):
    o=np.zeros(a.shape,np.uint8); o[np.isin(a,SK)]=1; o[np.isin(a,FU)]=2; o[np.isin(a,BL)]=3; o[np.isin(a,(1,111,112))]=4; return o
seen=set(); pairs=[]
for s_,k in n.items():
    if s_>=22: continue
    for f in range(k):
        for d in range(3):
            c=R.frame(AID,s_,f,d)
            if not c.any() or c.tobytes() in seen: continue
            seen.add(c.tobytes())
            o=fr(s_,f,d,'mix'); a,b=cls(c),cls(o)
            ch=((a!=b)&(a!=4)&(b!=4)&(a>0)&(b>0)).sum()
            if ch>=2: pairs.append((s_,f,d))
print(len(pairs),'frames with a hand or an arm changed:',pairs)
BX=(64-42,64+10,48-24,48+28)
def c2(c): return R.rgb(c[BX[0]:BX[1],BX[2]:BX[3]])
per=5; Zh=4; cells=[np.concatenate([c2(fr(s_,f,d,'now')),c2(fr(s_,f,d,'mix'))],1) for s_,f,d in pairs]
blank=np.zeros_like(cells[0]); blank[:]=BG
rws=[np.concatenate(cells[i:i+per]+[blank]*(per-len(cells[i:i+per])),1) for i in range(0,len(cells),per)]
big(np.concatenate(rws,0),Zh).save(out+'/ssj4_goku_hands_and_arms_now_and_new.png')
def gif(name,rows_,seq,ms=120,z=5,reps=3,labels=None):
    frames=[]
    for _ in range(reps):
        for slot,f in seq:
            im=np.concatenate([np.concatenate([cell(fr(slot,min(f,n[slot]-1),d,kind),m) for kind,d,m in r],1) for r in rows_],0); p=big(im,z)
            if labels:
                dd=ImageDraw.Draw(p)
                for (x,y),t in labels: dd.text((x*z+4,y*z+3),t,fill=(255,255,255),font=FS)
            frames.append(p)
    frames[0].save(out+'/'+name,save_all=True,append_images=frames[1:],duration=ms,loop=0,disposal=2)
def three(kind): return [(kind,0,False),(kind,2,False),(kind,1,False)]
FSB=[((2,1),'front'),((CW+2,1),'side'),((2*CW+2,1),'back')]
idle=[(0,0),(0,1)]*6
gif('ssj4_goku_idle_now_and_new.gif',[three('now'),three('mix')],idle,ms=300,z=5,reps=2,labels=[((2,1),'now'),((2,CH+1),'new')])
walkrun=[(1,f) for f in range(n[1])]*2+[(2,f) for f in range(n[2])]*2
blast=[(0,0)]*2+[(3,f) for f in range(n[3])]+[(3,n[3]-1)]*2+[(0,0)]*2+[(18,f) for f in range(n[18])]+[(18,n[18]-2),(18,n[18]-1)]*2+[(0,0)]*2
combo=[(0,0)]+[(s,f) for s in (4,5,6) for f in range(n[s])]+[(0,0)]
kame=[(0,0)]*2+[(18,f) for f in range(n[18])]+[(18,n[18]-2),(18,n[18]-1)]*3+[(0,0)]*2
gif('ssj4_goku_kamehameha_front_now_and_new.gif',[[('now',0,False),('mix',0,False),('daima_pic',0,False)]],kame,ms=150,z=6,labels=[((2,1),'now'),((CW+2,1),'new'),((2*CW+2,1),'Daima')])
power=[(0,0)]*2+[(13,0)]*3+[(13,1)]*4+[(13,0)]*2+[(0,0)]*2
gif('ssj4_goku_arms_raised_now_new_and_daima.gif',[[('now',0,False),('mix',0,False),('daima_pic',0,False)]],power,ms=160,z=6,labels=[((2,1),'now'),((CW+2,1),'new'),((2*CW+2,1),'Daima')])
gif('ssj4_goku_new_walk_and_run.gif',[three('mix')],walkrun,labels=FSB)
gif('ssj4_goku_new_ki_blast_and_kamehameha.gif',[three('mix')],blast,ms=140,labels=FSB)
gif('ssj4_goku_new_combo.gif',[three('mix')],combo,ms=140,labels=FSB)
DL=FSB
gif('ssj4_goku_daima_walk_and_run.gif',[three('daima_pic')],walkrun,labels=DL)
gif('ssj4_goku_daima_ki_blast_and_kamehameha.gif',[three('daima_pic')],blast,ms=140,labels=DL)
gif('ssj4_goku_daima_combo.gif',[three('daima_pic')],combo,ms=140,labels=DL)
def strip(kind,d,name,z=3,per=11):
    lines=[]; cur=[]
    for s,k in n.items():
        if s>=22: continue
        cells=[cell(fr(s,f,d,kind)) for f in range(k)]
        if cur and len(cur)+len(cells)>per: lines.append(cur); cur=[]
        cur+=cells
        while len(cur)>per: lines.append(cur[:per]); cur=cur[per:]
    if cur: lines.append(cur)
    w=max(len(x) for x in lines); blank=np.zeros_like(lines[0][0]); blank[:]=BG
    im=np.concatenate([np.concatenate(x+[blank]*(w-len(x)),1) for x in lines],0)
    big(im,z).save(out+'/'+name)
for kind,nm in (('mix','new'),('daima_pic','daima')):
    for d,v in ((0,'front'),(2,'side'),(1,'back')): strip(kind,d,'ssj4_goku_%s_every_%s_frame.png'%(nm,v))
print(sorted(os.listdir(out)))
