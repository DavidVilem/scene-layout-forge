"""Original procedural graphite marks; no embedded or external artwork."""
import numpy as np
from PIL import Image


def surface_coordinates(world, spec, surface_map=None):
    """Local planar/cylindrical coordinates shared by every face of an owner.

    Rigid frames follow explicit owner transforms. Registered UVs instead follow
    actual indexed triangle vertices via a validated barycentric surface map.
    """
    if spec.get('mapping') == 'registered':
        if surface_map is None: raise ValueError('registered material needs its actual triangle surface map')
        return surface_map.coordinates(world)
    p = np.asarray(world, float) - np.asarray(spec.get('origin', [0, 0, 0]), float)
    axis = np.asarray(spec.get('axis', [0, 0, 1]), float); axis /= np.linalg.norm(axis)
    tangent = np.asarray(spec.get('tangent', [1, 0, 0]), float); tangent /= np.linalg.norm(tangent)
    other = np.cross(axis, tangent)
    x, y, z = p@tangent, p@other, p@axis
    if spec.get('mapping', 'planar') == 'cylindrical':
        # Periodic angular phase: neighboring facets and the seam agree.
        return np.arctan2(y, x)/(2*np.pi), z
    return x + y, z


def surface_hatching(world, spec, normal, color, surface_map=None):
    """Economic material marks on registered surfaces; fill-only output."""
    u, v = surface_coordinates(world, spec, surface_map)
    spacing = spec.get('spacing', .12); density = spec.get('density', .12)
    family = spec['family']; mark = spec.get('mark', 'auto')
    if mark == 'auto':
        mark = {'matte_metal': 'axial', 'glass': 'none', 'concrete': 'stipple',
                'wood': 'grain', 'stone': 'stipple', 'cloth': 'cross', 'rubber': 'axial'}[family]
        axis=np.asarray(spec.get('axis',[0,0,1]),float);axis/=np.linalg.norm(axis)
        n=np.asarray(normal,float);n/=max(np.linalg.norm(n),1e-12)
        if spec.get('mapping','planar') == 'planar' and abs(n@axis)>.95:
            tangent=np.asarray(spec.get('tangent',[1,0,0]),float);tangent/=np.linalg.norm(tangent)
            p=np.asarray(world,float)-np.asarray(spec.get('origin',[0,0,0]),float)
            u,v=p@tangent,p@np.cross(axis,tangent)
            if family=='wood':mark='endgrain'
    if mark == 'none' or density == 0: return np.zeros_like(u)
    cyclic = spec.get('mapping') == 'cylindrical'
    # A whole integer number of angular strokes keeps the seam continuous.
    period = max(4, round(1/spacing))
    a = u * period if cyclic else u/spacing
    b = v/spacing
    def stripes(phase):
        # Analytic pixel footprint is approximated from the local parameter field.
        dx = np.diff(phase, axis=1, append=phase[:, -1:]) if phase.ndim == 2 else 0
        dy = np.diff(phase, axis=0, append=phase[-1:, :]) if phase.ndim == 2 else 0
        if cyclic:
            dx = dx - np.round(dx/period)*period
            dy = dy - np.round(dy/period)*period
        dx, dy = np.abs(dx), np.abs(dy)
        footprint = np.clip(dx+dy, .03, 1)
        def integral(t): return np.floor(t)*density + np.minimum(np.mod(t, 1), density)
        return (integral(phase+footprint/2)-integral(phase-footprint/2))/footprint
    if mark == 'endgrain': phase = np.sqrt(a*a+b*b)
    elif mark == 'grain': phase = a + .15*np.sin(b*.35)
    elif mark == 'stipple':
        # Deterministic irregular grain; no image assets and no camera-space seed.
        value = np.sin(np.floor(a)*127.1 + np.floor(b)*311.7)*43758.5453
        dots = (np.mod(value, 1) < density) * np.maximum(0, 1-3*np.hypot(np.mod(a, 1)-.5, np.mod(b, 1)-.5))
        return dots*(12 if family == 'concrete' else 20)
    else: phase = a
    marks = stripes(phase)
    if mark == 'cross': marks += stripes(b)*.65
    darkness = float(np.clip((250-float(color[0]))/100, 0, 1))
    return marks*(4+24*darkness)


def paper_grain(width,height,pixel_ratio,seed=0):
    rng=np.random.default_rng(941+seed)
    field=np.zeros((height,width),dtype=np.float32)
    for spacing,weight in [(90,.9),(14,1.4),(3,.65)]:
        rows=max(3,int(height/(spacing*pixel_ratio))+2)
        cols=max(3,int(width/(spacing*pixel_ratio))+2)
        samples=rng.normal(0,1,(rows,cols)).astype(np.float32)
        field+=np.asarray(Image.fromarray(samples).resize((width,height),Image.Resampling.BICUBIC))*weight
    field+=rng.normal(0,.65,(height,width)).astype(np.float32)
    return np.clip(field,-10,10)


def hatch_pressure(x,y,pixel_ratio,phase):
    # Pressure varies along each fill stroke. Geometric contour coordinates
    # are never perturbed, and this function cannot change depth or ownership.
    stripe=np.floor(phase)
    return .48+.52*(.5+.5*np.sin(x/(17*pixel_ratio)+stripe*1.618+y/(109*pixel_ratio)))


def graphite_hatching(x,y,pixel_ratio,normal,color):
    """Screen-space pencil fill, shared by coplanar triangles.

    Absolute normal components keep winding changes from changing the marks.
    Broad lit planes receive sparse, light strokes; darker planes get a second
    restrained stroke family. Only fill intensity is returned, never geometry.
    """
    n=np.abs(np.asarray(normal,dtype=float))
    n/=max(float(np.linalg.norm(n)),1e-12)
    darkness=float(np.clip((242-float(color[0]))/28,0,1))
    # Keep phase/spacing independent of tone and horizontal normal angle:
    # varying either makes adjacent cylinder facets acquire broken stripes.
    spacing=10*pixel_ratio
    slope=.35+.65*n[2]
    def strokes(slope,spacing,offset):
        phase=(x+slope*y)/spacing+offset
        footprint=(1+abs(slope))/spacing
        def integral(t):return np.floor(t)*.10+np.minimum(np.mod(t,1),.10)
        coverage=(integral(phase+footprint/2)-integral(phase-footprint/2))/footprint
        return coverage*hatch_pressure(x,y,pixel_ratio,phase)
    primary=strokes(slope,spacing,0)
    secondary=strokes(-.75,spacing*1.35,.37)
    return (primary+secondary*max(0,darkness-.45))*(3+25*darkness)


def contour_ink(x,y,depth,depth_range,pixel_ratio):
    lo,hi=depth_range
    near=np.clip((depth-lo)/max(hi-lo,1e-12),0,1)
    near=np.where(np.isfinite(near),near,.5)
    pressure=8*np.sin(x/(23*pixel_ratio)+y/(41*pixel_ratio))
    value=104-43*near+pressure
    return np.stack([value,value,value],axis=-1).clip(0,255).astype(np.uint8)


def finish_paper(rgb,pixel_ratio,seed=0):
    height,width=rgb.shape[:2]
    grain=paper_grain(width,height,pixel_ratio,seed)
    # Lighter pressure on dark ink keeps fine contours legible through grain.
    amount=.35+.65*np.mean(rgb,axis=2)/255
    return np.clip(rgb.astype(np.float32)+(grain*amount)[...,None],0,255).astype(np.uint8)
