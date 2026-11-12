"""Scratch: frames of an actor of a built ROM as index arrays on a canvas round the actor's origin."""
import sys, struct
sys.path[:0]=['ultimate','ultimate/lib','tools/scripts']
import numpy as np
from PIL import Image
import goku_black
B=0x08000000
class Rom:
    def __init__(self, path):
        self.rom=open(path,'rb').read(); clean=open('baserom.gba','rb').read()
        self.pal=np.frombuffer(clean[0x701B0+768:0x701B0+1536],np.uint8).reshape(256,3).copy(); self.lst=self.u(0x3C0)-4-B
    def u(self,o): return struct.unpack_from('<I',self.rom,o)[0]
    def slots(self,aid):
        rec=self.u(self.lst+4*aid)-B; out={}
        for s in range(self.rom[rec]):
            an=self.u(rec+0x54+4*s)
            if an: out[s]=self.u(an-B)
        return out
    def frame(self,aid,slot,f,d,size=(96,96),origin=(64,48)):
        rec=self.u(self.lst+4*aid)-B; an=self.u(rec+0x54+4*slot)-B; fp=self.u(an+4+4*(4*f+d))
        c=np.zeros(size,np.uint8)
        if not fp: return c
        o=fp-B
        for i in range(self.u(o)):
            p=o+8+12*i; x,y,w,h=struct.unpack_from('<bbBB',self.rom,p); img=goku_black.tiles(self.rom,self.u(p+8)-B,w,h)
            if struct.unpack_from('<H',self.rom,p+6)[0]&0x1000: img=img[:,::-1]
            m=img>0; c[origin[0]+y:origin[0]+y+h,origin[1]+x:origin[1]+x+w][m]=img[m]
        return c
    def rgb(self,c,bg=(88,120,88)):
        o=self.pal[c].copy(); o[c==0]=bg; return o.astype(np.uint8)
def crop(c,pad=0):
    ys,xs=np.nonzero(c); return c[max(ys.min()-pad,0):ys.max()+1+pad, max(xs.min()-pad,0):xs.max()+1+pad]
def show(c):
    for y,r in enumerate(c): print('%2d '%y+' '.join('%3d'%v if v else '  .' for v in r))
