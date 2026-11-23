#!/usr/bin/env python3
"""Generate the KRUZENLAB K-01 cyber-helmet mascot as an ASCII STL mesh.

No third-party packages are required. Coordinates are in arbitrary model units.
Run from any directory: python clawd/make_stl.py [output.stl]
"""
from math import sin, cos, pi
from pathlib import Path
import sys

TRIS = []

def tri(a, b, c):
    TRIS.append((a, b, c))

def ellipsoid(center, radii, rings=18, segments=32):
    cx, cy, cz = center
    rx, ry, rz = radii
    for i in range(rings):
        lat0 = -pi/2 + pi*i/rings
        lat1 = -pi/2 + pi*(i+1)/rings
        for j in range(segments):
            lon0 = 2*pi*j/segments
            lon1 = 2*pi*(j+1)/segments
            def v(lat, lon):
                return (cx+rx*cos(lat)*cos(lon),
                        cy+ry*sin(lat),
                        cz+rz*cos(lat)*sin(lon))
            a,b,c,d = v(lat0,lon0),v(lat1,lon0),v(lat1,lon1),v(lat0,lon1)
            tri(a,b,c); tri(a,c,d)

def cylinder(a, b, radius, segments=20):
    """Closed cylinder between 3D points."""
    import math
    ax,ay,az=a; bx,by,bz=b
    dx,dy,dz=bx-ax,by-ay,bz-az
    length=math.sqrt(dx*dx+dy*dy+dz*dz)
    ux,uy,uz=dx/length,dy/length,dz/length
    # stable perpendicular basis
    ref=(0,1,0) if abs(uy)<0.9 else (1,0,0)
    vx=uy*ref[2]-uz*ref[1]; vy=uz*ref[0]-ux*ref[2]; vz=ux*ref[1]-uy*ref[0]
    vl=math.sqrt(vx*vx+vy*vy+vz*vz); vx,vy,vz=vx/vl,vy/vl,vz/vl
    wx=uy*vz-uz*vy; wy=uz*vx-ux*vz; wz=ux*vy-uy*vx
    ring1=[]; ring2=[]
    for i in range(segments):
        t=2*pi*i/segments
        off=tuple(radius*(cos(t)*v+sin(t)*w) for v,w in zip((vx,vy,vz),(wx,wy,wz)))
        ring1.append(tuple(a[k]+off[k] for k in range(3)))
        ring2.append(tuple(b[k]+off[k] for k in range(3)))
    for i in range(segments):
        n=(i+1)%segments
        tri(ring1[i],ring2[i],ring2[n]); tri(ring1[i],ring2[n],ring1[n])
        tri(a,ring1[n],ring1[i]); tri(b,ring2[i],ring2[n])

def rounded_panel(center, size, bevel=0.12):
    """Low-poly beveled rectangular shell built as an ellipsoid-like octagonal prism."""
    cx,cy,cz=center; sx,sy,sz=size
    # octagonal cross-section in X/Z, extruded along Y
    outline=[(-sx+bevel,-sz),(sx-bevel,-sz),(sx,-sz+bevel),(sx,sz-bevel),
             (sx-bevel,sz),(-sx+bevel,sz),(-sx,sz-bevel),(-sx,-sz+bevel)]
    front=[(cx+x,cy-sy,cz+z) for x,z in outline]
    back=[(cx+x,cy+sy,cz+z) for x,z in outline]
    fc=(cx,cy-sy,cz); bc=(cx,cy+sy,cz)
    for i in range(8):
        n=(i+1)%8
        tri(fc,front[i],front[n]); tri(bc,back[n],back[i])
        tri(front[i],back[i],back[n]); tri(front[i],back[n],front[n])

# Main helmet: broad domed shell, lower chin ring, and a deep front visor.
ellipsoid((0,0.10,0.05),(0.92,0.76,0.76),22,40)
ellipsoid((0,-0.28,0.12),(0.82,0.43,0.68),16,36)
rounded_panel((0,-0.655,0.17),(0.66,0.075,0.29),0.18)  # visor frame
ellipsoid((0,-0.735,0.18),(0.56,0.045,0.205),12,36)   # glass visor
# paired glowing eye modules represented as raised lenses
for x in (-0.245,0.245):
    ellipsoid((x,-0.785,0.205),(0.105,0.035,0.075),10,20)
# crown crest + antenna and beacon
ellipsoid((0,0.78,0.06),(0.27,0.16,0.24),12,24)
cylinder((0,0.88,0.06),(0,1.20,0.06),0.055,16)
ellipsoid((0,1.25,0.06),(0.12,0.12,0.12),12,20)
# side audio/processor pods and tiny side fins
for s in (-1,1):
    ellipsoid((s*0.88,0.05,0.02),(0.20,0.32,0.35),14,24)
    ellipsoid((s*1.02,0.05,0.02),(0.075,0.19,0.22),10,20)
    # angled ear fins
    cylinder((s*0.83,0.34,0.0),(s*1.18,0.58,0.0),0.09,12)
# lower floating stabilizer / neck ring
ellipsoid((0,-0.72,0.08),(0.42,0.12,0.38),12,28)

def normal(a,b,c):
    ux,uy,uz=(b[i]-a[i] for i in range(3))
    vx,vy,vz=(c[i]-a[i] for i in range(3))
    nx,ny,nz=uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx
    l=(nx*nx+ny*ny+nz*nz)**0.5 or 1
    return nx/l,ny/l,nz/l

def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"assets"/"kruzen_bot.stl"
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="ascii") as f:
        f.write("solid kruzen_k01_cyber_helmet\n")
        for a,b,c in TRIS:
            n=normal(a,b,c)
            f.write(" facet normal %.6f %.6f %.6f\n  outer loop\n"%n)
            for p in (a,b,c): f.write("   vertex %.5f %.5f %.5f\n"%p)
            f.write("  endloop\n endfacet\n")
        f.write("endsolid kruzen_k01_cyber_helmet\n")
    print(f"Generated {out} ({len(TRIS)} triangles)")

if __name__=="__main__":
    main()
