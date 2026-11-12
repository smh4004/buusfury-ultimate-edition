"""Super Saiyan 4 Gogeta's idle, walk and run as they are and with fixes.py's fixes, for the owner to look at (whole figures on the game's
green, no markings): a still per view, GIFs of the walk and the run, and his side head close.
  BFU_GOG_ROM=<debug build> python3 ultimate/gogeta_preview/preview.py <out dir>"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview'), os.path.join(HERE, '..')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fixed as look
from frames import fr, GOG, NS, R
OUT=sys.argv[1]; BG=(88,120,88); BOX=(37,72,41,78); H=BOX[1]-BOX[0]; W=BOX[3]-BOX[2]
F=ImageFont.load_default(size=16); FS=ImageFont.load_default(size=13)
def cell(c):
    c=c[BOX[0]:BOX[1],BOX[2]:BOX[3]]; rgb=R.rgb(c).copy(); rgb[c==0]=BG; return rgb
now=lambda k: cell(fr(GOG,*k)); new=lambda k: cell(look.fixed(k))
big=lambda im,z: Image.fromarray(im).resize((im.shape[1]*z,im.shape[0]*z),Image.NEAREST)
VIEWS=((2,'side'),(1,'back'),(0,'front'))
def still(d,name,z=6):
    lines=[[(0,0,d)]+[(1,f,d) for f in range(4)],[(2,f,d) for f in range(4)]]; band=22
    Wp=5*W*z; img=Image.new('RGB',(Wp,4*H*z+4*band),BG); dr=ImageDraw.Draw(img); y=0
    for li,line in enumerate(lines):
        for what,fn in (('now',now),('fixed',new)):
            dr.rectangle((0,y,Wp,y+band),fill=(30,40,30))
            dr.text((6,y+2),'%s, %s: %s'%(name,('standing and walk','run')[li],what),fill=(255,255,255),font=F); y+=band
            row=np.concatenate([fn(k) for k in line],1); img.paste(big(row,z),(0,y)); y+=H*z
    return img
def gif(path,seq,ms=130,z=5,reps=3):
    frames=[]; band=20
    for _ in range(reps):
        for s,f in seq:
            img=Image.new('RGB',(3*W*z,2*H*z+2*band),BG); dr=ImageDraw.Draw(img); y=0
            for what,fn in (('now',now),('fixed',new)):
                dr.rectangle((0,y,3*W*z,y+band),fill=(30,40,30))
                for i,(d,v) in enumerate(VIEWS): dr.text((i*W*z+6,y+2),'%s, %s'%(what,v),fill=(255,255,255),font=FS)
                y+=band; img.paste(big(np.concatenate([fn((s,f,d)) for d,_ in VIEWS],1),z),(0,y)); y+=H*z
            frames.append(img)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=ms,loop=0)
for d,v in VIEWS: still(d,'from the '+v if v!='back' else 'from behind').save('%s/ssj4_gogeta_%s_now_and_fixed.png'%(OUT,v))
gif(OUT+'/ssj4_gogeta_walk_now_and_fixed.gif',[(1,f) for f in range(4)],ms=150)
gif(OUT+'/ssj4_gogeta_run_now_and_fixed.gif',[(2,f) for f in range(4)],ms=110)
gif(OUT+'/ssj4_gogeta_stand_walk_run_now_and_fixed.gif',[(0,0)]*4+[(1,f) for f in range(4)]*2+[(0,0)]*2+[(2,f) for f in range(4)]*3,ms=130,reps=1)
# from behind alone, bigger: now beside fixed (the owner, 22:25: "The back ones still doing it it's by a pixel or two moving slightly to the side")
def gif_back(path,seq,ms,z=8,reps=3):
    frames=[]; band=22
    for _ in range(reps):
        for s,f in seq:
            img=Image.new('RGB',(2*W*z,H*z+band),BG); dr=ImageDraw.Draw(img); dr.rectangle((0,0,2*W*z,band),fill=(30,40,30))
            dr.text((6,3),'now',fill=(255,255,255),font=F); dr.text((W*z+6,3),'fixed',fill=(255,255,255),font=F)
            img.paste(big(np.concatenate([now((s,f,1)),new((s,f,1))],1),z),(0,band)); frames.append(img)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=ms,loop=0)
gif_back(OUT+'/ssj4_gogeta_from_behind_walk_now_and_fixed.gif',[(1,f) for f in range(4)],170)
gif_back(OUT+'/ssj4_gogeta_from_behind_run_now_and_fixed.gif',[(2,f) for f in range(4)],120)
# his head from the side, close: the see-through spot over his eye
z=14; hb=(40,57,44,64)
def head(c):
    c=c[hb[0]:hb[1],hb[2]:hb[3]]; rgb=R.rgb(c).copy(); rgb[c==0]=BG; return rgb
k=(0,0,2); pair=np.concatenate([head(fr(GOG,*k)),head(look.fixed(k))],1); im=big(pair,z)
out=Image.new('RGB',(im.width,im.height+24),(30,40,30)); out.paste(im,(0,24)); dr=ImageDraw.Draw(out)
dr.text((6,3),'now: the ground shows through over his eye',fill=(255,255,255),font=FS); dr.text((im.width//2+6,3),'fixed',fill=(255,255,255),font=FS)
out.save(OUT+'/ssj4_gogeta_head_from_the_side_now_and_fixed.png')
print(sorted(os.listdir(OUT)))
