"""Disjoint heightfield mountain cells surrounding a real section cavity.

Contextual geological form and explicit geometric contact evidence only. This is
not a rock stability, excavation, reinforcement or geotechnical design adapter.
"""
import math


def _heightfield_part(name,x0,x1,y0,y1,z0,height,spacing=6):
    """Closed solid with planar base and sampled triangulated upper surface."""
    nx=max(1,math.ceil((x1-x0)/spacing));ny=max(1,math.ceil((y1-y0)/spacing))
    xs=[x0+(x1-x0)*i/nx for i in range(nx+1)];ys=[y0+(y1-y0)*j/ny for j in range(ny+1)]
    verts=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]]
    def at(i,j):return 4+i*(ny+1)+j
    for x in xs:
        for y in ys:
            z=height(x,y)
            if z<=z0+1e-5:raise ValueError('terrain surface must remain above its base')
            verts.append([x,y,z])
    faces=[[0,3,2,1]];edges=[[0,1],[1,2],[2,3],[3,0]]
    for i in range(nx):
        for j in range(ny):
            a,b,c,d=at(i,j),at(i+1,j),at(i+1,j+1),at(i,j+1)
            faces += [[a,b,c],[a,c,d]]
    boundary=[at(i,0) for i in range(nx+1)]+[at(nx,j) for j in range(1,ny+1)]+[at(i,ny) for i in range(nx-1,-1,-1)]+[at(0,j) for j in range(ny-1,0,-1)]
    # Each boundary sample has a corresponding base point. Separate triangles
    # close the sides without a nonplanar polygon fan or oversized bounding slab.
    base_indices=[]
    for index in boundary:
        x,y,_=verts[index];base_indices.append(len(verts));verts.append([x,y,z0])
    for n,a in enumerate(boundary):
        m=(n+1)%len(boundary);b=boundary[m];aa=base_indices[n];bb=base_indices[m]
        faces += [[aa,bb,b],[aa,b,a]];edges.append([a,b])
    for i,j in ((0,0),(nx,0),(nx,ny),(0,ny)):
        index=at(i,j);base=base_indices[boundary.index(index)];edges.append([base,index])
    top=max(v[2] for v in verts)
    return {'id':name,'kind':'custom','origin':[x0,y0,z0],'size':[x1-x0,y1-y0,top-z0],
        'semantic_role':'geological_envelope','parameters':{'adapter':'mountain-heightfield-cell',
        'vertices':[[x-x0,y-y0,z-z0] for x,y,z in verts],'faces':faces,'edges':edges,
        'limitations':'sampled heightfield and flat contact geometry; no geological material model, stability or excavation certification'}}


def build_mountain_section(cavity_half=17,roof_z=21.5,extent=42,prefix='mountain'):
    """Return a complete mountain fragment and explicit display-only removal IDs.

    The cavity is empty down through z=-.4 for foundations. Ground roots use
    slabs only in the outside ring. A contextual subsurface band meets that ring
    laterally below z=-.4; no foundation bearing claim is inferred from proximity.
    Source roof bands bridge between separate sampled planar support interfaces.
    Their load-bearing/geotechnical behavior is deliberately not certified.
    """
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (cavity_half,roof_z,extent)):
        raise ValueError('finite terrain dimensions required')
    if cavity_half<=5 or roof_z<5 or extent<=cavity_half+10:raise ValueError('terrain dimensions leave no cavity or slope')
    inner=cavity_half;rim=inner+3;cap=.2;solid_top=roof_z-cap
    s={'units':'m','schema_version':2,'validation_policy':'strict','registered_geometry':True,
       'parts':[],'grounded':[],'bearings':[],'mounts':[],'custom_contacts':[],'display_hidden':[]}
    def add(p):s['parts'].append(p);return p
    def slab(name,x0,x1,y0,y1,z,thick):
        return add({'id':name,'kind':'slab','origin':[x0,y0,z],'size':[x1-x0,y1-y0,thick]})
    def patch(part,on,x0,x1,y0,y1,z):
        margin=min(.2,(x1-x0)/5,(y1-y0)/5)
        s['custom_contacts'].append({'part':part,'on':on,'points':[
            [x0+margin,y0+margin,z],[x1-margin,y0+margin,z],
            [x1-margin,y1-margin,z],[x0+margin,y1-margin,z]]})
    def ground_solid(name,x0,x1,y0,y1,height,hidden,base_depth=.2):
        base=slab(name+'/ground',x0,x1,y0,y1,-base_depth,base_depth);s['grounded'].append(base['id'])
        rock=add(_heightfield_part(name,x0,x1,y0,y1,0,height))
        patch(name,base['id'],x0,x1,y0,y1,0)
        if hidden:s['display_hidden'] += [name,base['id']]
        return rock
    # Four non-overlapping inner ring regions: actual empty cavity, no shared
    # scene-sized AABB through the building.
    ring=[('west',-rim,-inner,-rim,rim,False),('east',inner,rim,-rim,rim,True),
          ('south',-inner,inner,-rim,-inner,True),('north',-inner,inner,inner,rim,False)]
    caps={}
    for side,x0,x1,y0,y1,hidden in ring:
        name=prefix+'/inner-'+side
        rock=ground_solid(name,x0,x1,y0,y1,lambda x,y:solid_top,hidden,base_depth=3)
        support=slab(name+'/interface',x0,x1,y0,y1,solid_top,cap)
        support['semantic_role']='sampled_geological_contact_layer'
        s['bearings'].append({'part':support['id'],'on':rock['id']});caps[side]=support['id']
        if hidden:s['display_hidden'].append(support['id'])
    # Two exposed geological bands close the lower section. Their horizontal
    # contact with each other and vertical contact with the surrounding ring are
    # explicit geometry. The upper band stops at the deepest foundation bottom;
    # rooms whose foundations end higher retain an unverified subsurface gap.
    lower=slab(prefix+'/subsurface-lower',-inner,inner,-inner,inner,-3,1.4)
    upper=slab(prefix+'/subsurface-upper',-inner,inner,-inner,inner,-1.6,1.2)
    for p in (lower,upper):
        p['semantic_role']='contextual_subsurface_rock'
        p['material_note']='exposed geological section: irregular sediment/rock strata, not a concrete foundation'
    s['mounts'] += [
        {'part':lower['id'],'on':prefix+'/inner-west/ground','axis':'x','side':1},
        {'part':lower['id'],'on':prefix+'/inner-east/ground','axis':'x','side':-1}]
    s['bearings'].append({'part':upper['id'],'on':lower['id']})
    def roof_height(x,y):
        # Broad, off-center rounded crest. Unequal waves break rectangular ridge
        # silhouettes without adding noisy texture or changing the cavity.
        return roof_z+1.2+9*math.exp(-((x/(rim*1.05))**2+((y-rim*.3)/(rim*1.2))**2))+ .6*math.sin(x*.11)*math.cos(y*.08)
    def hillside(x,y):
        r=max(abs(x),abs(y))
        if r<=rim:return roof_height(x,y)
        q=extent-r;scale=rim/r
        return .06+(roof_height(x*scale,y*scale)-.06)*max(0,q/(extent-rim))**.85
    # Four supported roof bands can be selectively hidden for the section view;
    # each remains part of the complete physical envelope.
    bands=[-rim,-rim*.5,0,rim*.5,rim]
    for i,(y0,y1) in enumerate(zip(bands,bands[1:])):
        name=prefix+f'/crown-{i}';add(_heightfield_part(name,-rim,rim,y0,y1,roof_z,roof_height,spacing=4))
        patch(name,caps['west'],-rim,-inner,y0,y1,roof_z)
        patch(name,caps['east'],inner,rim,y0,y1,roof_z)
        if i<3:s['display_hidden'].append(name)
    # Independent surrounding cells meet at shared boundaries and slope toward
    # the apron. Every AABB is outside the cavity footprint.
    coordinates=[-extent,-(extent+rim)/2,-rim,rim,(extent+rim)/2,extent]
    for i,(x0,x1) in enumerate(zip(coordinates,coordinates[1:])):
        for j,(y0,y1) in enumerate(zip(coordinates,coordinates[1:])):
            if x0==-rim and x1==rim and y0==-rim and y1==rim:continue
            name=prefix+f'/slope-{i}-{j}'
            hidden=(x0>=rim or y1<=-rim) and not (x1<=-rim or y0>=rim)
            ground_solid(name,x0,x1,y0,y1,hillside,hidden)
    s['terrain_contract']={'type':'heightfield_with_cavity','cavity':{'min':[-inner,-inner,-.4],'max':[inner,inner,roof_z]},
        'physical_enclosure':'four side regions, supported crown bands, outer slopes and contextual subsurface bands ending at z=-.4',
        'section':'remove near east/south regions and front crown bands only in derived display scene',
        'limits':['geometric contact samples only','rock mechanics, geology, excavation support and roof-span stability not verified',
                  'subsurface band does not establish bearing under room foundations ending at z=-.2; that intervening space is unverified']}
    return s
