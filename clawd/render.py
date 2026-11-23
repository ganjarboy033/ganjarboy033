#!/usr/bin/env python3
"""Ray-marched KRUZENLAB K-01 mascot renderer.

Dependencies: numpy, Pillow. Example:
  python clawd/render.py 0 48
  python clawd/render.py 0 48 --gif assets/kruzen_bot.gif
Environment: W=480 H=360 N=48 SS=1 OUT=frames
"""
import argparse, os
import numpy as np
from PIL import Image

SS=int(os.getenv("SS","1"))
W0,H0=int(os.getenv("W","480")),int(os.getenv("H","360"))
W,H=W0*SS,H0*SS
N=int(os.getenv("N","48"))
BG=np.array([8,16,28],dtype=float)/255.0
SHELL=np.array([0.12,0.25,0.31])
GLASS=np.array([0.015,0.07,0.10])
NEON=np.array([0.20,0.88,0.91])
GOLD=np.array([0.45,0.92,0.70])

def sd_ellipsoid(p,c,r):
    q=(p-np.asarray(c))/np.asarray(r)
    k0=np.linalg.norm(q,axis=-1)
    k1=np.linalg.norm(q/np.asarray(r),axis=-1)
    return k0*(k0-1.0)/(k1+1e-8)

def sd_roundbox(p,c,b,r):
    q=np.abs(p-np.asarray(c))-np.asarray(b)
    return np.linalg.norm(np.maximum(q,0),axis=-1)+np.minimum(np.max(q,axis=-1),0)-r

def sd_capsule(p,a,b,r):
    pa=p-np.asarray(a); ba=np.asarray(b)-np.asarray(a)
    h=np.clip(np.sum(pa*ba,axis=-1)/(np.dot(ba,ba)+1e-9),0,1)
    return np.linalg.norm(pa-h[...,None]*ba,axis=-1)-r

def rot_y(p,a):
    c,s=np.cos(a),np.sin(a)
    return np.stack((c*p[...,0]+s*p[...,2],p[...,1],-s*p[...,0]+c*p[...,2]),axis=-1)

def scene(p,t):
    phase=2*np.pi*t
    yaw=.24*np.sin(phase)
    bob=.045*np.sin(2*phase)
    q=rot_y(p-np.array([0,bob,0]),-yaw)
    # domed helmet and lower chin
    shell=sd_ellipsoid(q,(0,.10,.05),(.92,.76,.76))
    chin=sd_ellipsoid(q,(0,-.28,.12),(.82,.43,.68))
    d=np.minimum(shell,chin); material=np.zeros(d.shape,dtype=np.int8)
    # visor glass, wide horizontal panel
    visor=sd_roundbox(q,(0,-.665,.18),(.62,.075,.255),.12)
    visor=np.minimum(visor,sd_ellipsoid(q,(0,-.735,.18),(.56,.045,.205)))
    mask=visor<d; d=np.minimum(d,visor); material=np.where(mask,1,material)
    # side processor pods
    for side in (-1,1):
        pod=sd_ellipsoid(q,(side*.88,.05,.02),(.20,.32,.35))
        mask=pod<d; d=np.minimum(d,pod); material=np.where(mask,2,material)
        fin=sd_capsule(q,(side*.83,.34,0),(side*1.18,.58,0),.09)
        d=np.minimum(d,fin)
    # crown crest, antenna and beacon
    crest=sd_ellipsoid(q,(0,.78,.06),(.27,.16,.24))
    d=np.minimum(d,crest)
    antenna=sd_capsule(q,(0,.86,.06),(0,1.20,.06),.055)
    d=np.minimum(d,antenna)
    beacon=sd_ellipsoid(q,(0,1.25,.06),(.12,.12,.12))
    d=np.minimum(d,beacon)
    # eye lenses: two glowing pill-shaped apertures, gently pulse
    pulse=.85+.15*np.sin(phase*2)
    eye1=sd_ellipsoid(q,(-.245,-.785,.205),(.105,.035*pulse,.075))
    eye2=sd_ellipsoid(q,( .245,-.785,.205),(.105,.035*pulse,.075))
    eyes=np.minimum(eye1,eye2)
    mask=eyes<d; d=np.minimum(d,eyes); material=np.where(mask,3,material)
    # under-chin ring
    ring=sd_ellipsoid(q,(0,-.72,.08),(.42,.12,.38))
    d=np.minimum(d,ring)
    ground=p[...,1]+.92
    floor=ground<d
    return np.minimum(d,ground),np.where(floor,4,material)

def normal(p,t):
    e=.0018
    ex=np.array([e,0,0]); ey=np.array([0,e,0]); ez=np.array([0,0,e])
    n=np.stack([scene(p+ex,t)[0]-scene(p-ex,t)[0],
                scene(p+ey,t)[0]-scene(p-ey,t)[0],
                scene(p+ez,t)[0]-scene(p-ez,t)[0]],axis=-1)
    return n/(np.linalg.norm(n,axis=-1,keepdims=True)+1e-9)

def march(ro,rd,t):
    dist=np.zeros(len(ro)); hit=np.zeros(len(ro),bool); alive=np.ones(len(ro),bool)
    for _ in range(105):
        ids=np.where(alive)[0]
        if not len(ids): break
        d,_=scene(ro[ids]+rd[ids]*dist[ids,None],t)
        step=np.maximum(d*.82,.002)
        dist[ids]+=step
        done=(d<.0015)|(dist[ids]>18)
        hit[ids[d<.0015]]=True
        alive[ids[done]]=False
    return dist,hit

def shade_shadow(p,L,t):
    # soft shadow approximation toward the key light
    s=np.full(len(p),.035); shade=np.ones(len(p))
    for _ in range(24):
        d,_=scene(p+L*s[:,None],t)
        shade=np.minimum(shade,9*np.maximum(d,0)/(s+1e-6))
        s+=np.clip(d,.025,.22)
    return np.clip(shade,0,1)

def render(frame,outdir):
    t=frame/N
    cam=np.array([0.10,.55,3.85]); look=np.array([0,.10,0])
    f=look-cam; f/=np.linalg.norm(f)
    right=np.cross(f,[0,1,0]); right/=np.linalg.norm(right)
    up=np.cross(right,f)
    yy,xx=np.mgrid[0:H,0:W]
    px=(2*(xx+.5)-W)/H; py=-(2*(yy+.5)-H)/H
    rd=(px[...,None]*right+py[...,None]*up+1.82*f).reshape(-1,3)
    rd/=np.linalg.norm(rd,axis=-1,keepdims=True)
    ro=np.broadcast_to(cam,rd.shape).copy()
    pixels=np.broadcast_to(BG,(H*W,3)).copy()
    dist,hit=march(ro,rd,t)
    ids=np.where(hit)[0]
    if len(ids):
        p=ro[ids]+rd[ids]*dist[ids,None]
        _,mat=scene(p,t); n=normal(p,t)
        L=np.array([-.48,.82,.56]); L/=np.linalg.norm(L)
        diff=np.clip(np.sum(n*L,axis=-1),0,1)
        sh=shade_shadow(p+n*.006,L,t)
        view=-rd[ids]; halfv=L+view; halfv/=np.linalg.norm(halfv,axis=-1,keepdims=True)
        spec=np.clip(np.sum(n*halfv,axis=-1),0,1)**36
        rim=np.clip(1+np.sum(n*rd[ids],axis=-1),0,1)**2.5
        bases=np.tile(SHELL,(len(ids),1))
        bases=np.where((mat==1)[:,None],GLASS,bases)
        bases=np.where((mat==2)[:,None],np.array([.10,.39,.43]),bases)
        bases=np.where((mat==3)[:,None],NEON,bases)
        bases=np.where((mat==4)[:,None],BG,bases)
        ambient=.28+.32*np.clip(n[:,1]*.5+.5,0,1)
        color=bases*(ambient[:,None]+.78*(diff*sh)[:,None])
        color+=((.52*spec*sh)[:,None])*np.array([.65,.95,1.0])
        color+=((.22*rim)[:,None])*np.array([.08,.62,.78])
        # neon emissive eye and beacon highlights
        color=np.where((mat==3)[:,None],np.minimum(color+GOLD*.40,1),color)
        # ground receives a restrained cyan pool
        floor=mat==4
        if np.any(floor):
            glow=np.exp(-.55*(p[floor,0]**2+p[floor,2]**2))
            color[floor]=BG*(.72+.28*glow[:,None])
        pixels[ids]=np.clip(color,0,1)
    image=(pixels.reshape(H,W,3)*255).astype(np.uint8)
    Image.fromarray(image).resize((W0,H0),Image.Resampling.LANCZOS).save(os.path.join(outdir,f"frame_{frame:03d}.png"))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("start",type=int,nargs="?",default=0)
    parser.add_argument("end",type=int,nargs="?",default=N)
    parser.add_argument("--gif",default=None,help="Optional output GIF path")
    parser.add_argument("--fps",type=int,default=16)
    args=parser.parse_args()
    outdir=os.getenv("OUT","frames"); os.makedirs(outdir,exist_ok=True)
    for i in range(args.start,args.end):
        render(i,outdir); print(f"rendered frame {i}",flush=True)
    if args.gif:
        paths=[os.path.join(outdir,f"frame_{i:03d}.png") for i in range(args.start,args.end)]
        frames=[Image.open(p).convert("RGB") for p in paths]
        if frames:
            target=os.path.abspath(args.gif); os.makedirs(os.path.dirname(target),exist_ok=True)
            frames[0].save(target,save_all=True,append_images=frames[1:],duration=1000//max(1,args.fps),loop=0,optimize=True)
            print(f"GIF saved: {target}")

if __name__=="__main__":
    main()
