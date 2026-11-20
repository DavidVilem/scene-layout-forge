"""Depth-buffered orthographic architectural renderer. Pillow + NumPy."""
import argparse,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from scene_model import Part,validate,tower
from components import circulation
from architectural_parts import architecture
from technical_parts import technical
from drawing_style import graphite_hatching,contour_ink,finish_paper,surface_hatching
from surface_details import vessel_marks
from camera_geometry import clip_polygon,clip_segment,clip_screen_line
from sweep_geometry import check_tube_curvature

class Mesh:
    def __init__(self):self.faces=[];self.edges=[];self.smooth_edges=[];self.face_owners={};self.connection_names={}
    def ellipsoid(self,center,radii,n=24,rows=12):
        center=np.asarray(center,float);radii=np.asarray(radii,float)
        if center.shape!=(3,) or radii.shape!=(3,) or not np.isfinite(center).all() or not np.isfinite(radii).all() or min(radii)<=0 or n<4 or rows<3:
            raise ValueError('Invalid ellipsoid')
        vertices=[center+[0,0,radii[2]]]
        for j in range(1,rows):
            theta=math.pi*j/rows
            for i in range(n):
                phi=2*math.pi*i/n
                vertices.append(center+radii*np.array([math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)]))
        bottom=len(vertices);vertices.append(center-[0,0,radii[2]])
        faces=[]
        for i in range(n):faces.append([0,1+i,1+(i+1)%n])
        for j in range(rows-2):
            for i in range(n):
                a=1+j*n+i;b=1+j*n+(i+1)%n
                faces.append([a,a+n,b+n,b])
        for i in range(n):faces.append([bottom,1+(rows-2)*n+(i+1)%n,1+(rows-2)*n+i])
        adjacent={}
        for ids in faces:
            points=[vertices[i] for i in ids];self.faces.append((points,0))
            normal=np.cross(points[1]-points[0],points[2]-points[0])
            for a,b in zip(ids,ids[1:]+ids[:1]):adjacent.setdefault(tuple(sorted([a,b])),[]).append(normal)
        for (a,b),normals in adjacent.items():
            if len(normals)==2:self.smooth_edges.append((vertices[a],vertices[b],*normals))
    def sweep(self,points,radius,n=32,caps=True):
        ends=(caps,caps) if type(caps)==bool else caps
        if not isinstance(ends,(tuple,list)) or len(ends)!=2 or any(type(v)!=bool for v in ends):raise ValueError('caps must be bool or two booleans')
        pts=np.asarray(points,dtype=float)
        if pts.ndim!=2 or pts.shape[1]!=3 or len(pts)<2 or not np.isfinite(pts).all() or not math.isfinite(radius) or radius<=0 or n<3:raise ValueError('Invalid sweep dimensions')
        tangents=np.diff(pts,axis=0)
        if np.any(np.linalg.norm(tangents,axis=1)<1e-8):raise ValueError('Repeated sweep point')
        check_tube_curvature(pts,radius)
        tangents/=np.linalg.norm(tangents,axis=1)[:,None]
        ts=np.vstack([tangents[0],tangents[:-1]+tangents[1:],tangents[-1]])
        if np.any(np.linalg.norm(ts,axis=1)<1e-8):raise ValueError('Sweep reverses direction; split into separate routes')
        ts/=np.linalg.norm(ts,axis=1)[:,None]
        rings=[];previous=None
        for p,t in zip(pts,ts):
            if previous is None:
                axis=np.array([0.,0.,1.]) if abs(t[2])<.9 else np.array([1.,0.,0.])
                u=np.cross(t,axis);u/=np.linalg.norm(u)
            else:
                u=previous-t*np.dot(previous,t)
                if np.linalg.norm(u)<1e-8:
                    axis=np.eye(3)[np.argmin(np.abs(t))];u=np.cross(t,axis)
                u/=np.linalg.norm(u)
            v=np.cross(t,u);previous=u
            rings.append([p+radius*(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n)) for i in range(n)])
        for j in range(len(rings)-1):
            for i in range(n):
                k=(i+1)%n;self.faces.append(([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],0))
                normal=(rings[j][i]-pts[j])/radius
                prev=(rings[j][(i-1)%n]-pts[j])/radius
                nxt=(rings[j][k]-pts[j])/radius
                self.smooth_edges.append((rings[j][i],rings[j+1][i],normal+prev,normal+nxt))
        for closed,ring in zip(ends,[rings[0][::-1],rings[-1]]):
            if closed:self.faces.append((ring,0))
            self.edges.extend((ring[i],ring[(i+1)%n]) for i in range(n))
        return rings
    def flange(self,center,axis,radius,bolts=8,bore=0):
        center=np.asarray(center,float);axis=np.asarray(axis,float)
        if np.linalg.norm(axis)<1e-8 or radius<=0:raise ValueError('Invalid flange axis/radius')
        axis/=np.linalg.norm(axis);half=radius*.22
        if not math.isfinite(bore) or not 0<=bore<radius*1.6:raise ValueError('Invalid flange bore')
        outer=self.sweep([center-axis*half,center+axis*half],radius*1.6,32,caps=bore==0)
        ring=outer[1]
        if bore:
            inner=self.sweep([center-axis*half,center+axis*half],bore,32,caps=False)
            for end in (0,1):
                for i in range(32):
                    j=(i+1)%32
                    self.faces.append(([outer[end][i],outer[end][j],inner[end][j],inner[end][i]],0))
        u=np.array(ring[0])-center-axis*half;u/=np.linalg.norm(u);v=np.cross(axis,u)
        for i in range(bolts):
            angle=2*math.pi*i/bolts;p=center+radius*1.3*(u*math.cos(angle)+v*math.sin(angle))
            self.sweep([p-axis*half*1.4,p+axis*half*1.4],radius*.13,6)
    def box(self,origin,size,tone=0):
        o=np.array(origin,dtype=float);s=np.array(size,dtype=float)
        p=[o+s*np.array(v) for v in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
        for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.faces.append(([p[i] for i in ids],tone))
        for a,b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:self.edges.append((p[a],p[b]))

def build(data):
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    m=Mesh()
    if 'light_material_plan' in data:
        from visual_contract import LightMaterialPlan, _parse
        from dataclasses import asdict
        m.light_material_plan=asdict(_parse(LightMaterialPlan,data['light_material_plan']))
        unknown=set(m.light_material_plan['materials'])-{p['id'] for p in data['parts']}
        if unknown:raise ValueError('material owners absent from scene: '+', '.join(sorted(unknown)))
        from surface_mapping import material_errors
        for raw in data['parts']:
            problems=material_errors(raw,m.light_material_plan['materials'].get(raw['id'],{}))
            if problems:raise ValueError('; '.join(problems))
    # Explicit adapters only: never silently represent unsupported equipment as boxes.
    supported={'column','beam','slab','footing','wall','window','door','curtain_panel','mullion','parapet','landing','cabinet','paving','drain'}
    previous=None;start=0
    for raw in data['parts']:
        if previous is not None:
            m.face_owners.update({i:previous for i in range(start,len(m.faces))})
        start=len(m.faces);previous=raw['id']
        p=Part.from_data(raw)
        if p.kind=='custom':
            from registered_geometry import render as render_registered
            from surface_mapping import register_geometry
            render_registered(m,raw);register_geometry(m,raw,start);continue
        x,y,z=p.origin;w,d,h=p.size
        if technical(m,p):continue
        if circulation(m,p):continue
        if architecture(m,p):continue
        if p.kind=='manifold':
            ends=[True,True]
            raw=next(item for item in data['parts'] if item['id']==p.id)
            for spec in raw.get('interfaces',{}).values():
                if spec.get('termination')!='cap' and abs(spec['normal'][0])>.99:
                    ends[0 if spec['normal'][0]<0 else 1]=False
            m.sweep([(x,y+d/2,z+h/2),(x+w,y+d/2,z+h/2)],min(d,h)/2,32,caps=ends);continue
        if p.kind=='vessel':
            radius=min(w,d)/2;cx=x+w/2;cy=y+d/2
            leg_height=h/12;lid_base=z+h*35/36
            m.sweep([(cx,cy,z+leg_height),(cx,cy,lid_base)],radius,64)
            # Circumferential seams stay on the declared shell envelope. Fixed
            # outward rings previously invalidated clearance bounds at any size.
            for zz in [z+h*7/72,z+h*23/24]:m.sweep([(cx,cy,zz),(cx,cy,zz+h/90)],radius,64)
            m.sweep([(cx,cy,lid_base),(cx,cy,z+h)],radius*.35,32)
            leg_width=radius*2/17
            for dx in [-.6,.6]:
                for dy in [-.6,.6]:m.box((cx+dx*radius-leg_width/2,cy+dy*radius-leg_width/2,z),(leg_width,leg_width,leg_height))
            vessel_marks(m,p)
            continue
        if p.kind=='pump':
            base=h*.1875;body_radius=min(h*.3,d*.3,w*.24)
            m.box((x,y,z),(w,d,base))
            # Pedestals reach the casing and motor centre planes; the shaft
            # bridges the casing to the motor even for a long, shallow pump.
            m.box((x+w*.2,y+d*.35,z+base),(w*.1,d*.25,h*.5-base))
            m.box((x+w*.5,y+d*.42,z+base),(w*.2,d*.16,h*.5-base))
            m.sweep([(x+w*.25,y+d*.25,z+h*.5),(x+w*.25,y+d*.7,z+h*.5)],body_radius,32)
            m.sweep([(x+w*.25,y+d*.5,z+h*.5),(x+w*.45,y+d*.5,z+h*.5)],min(w,d,h)*.06,24)
            m.sweep([(x+w*.4,y+d*.5,z+h*.5),(x+w*.85,y+d*.5,z+h*.5)],min(h,d)*.24,32)
            for i in range(7):
                xx=x+w*(.42+i*.06);m.sweep([(xx,y+d*.5,z+h*.5),(xx+w/60,y+d*.5,z+h*.5)],min(h,d)*.26,24)
            continue
        if p.kind in {'pipe','conduit'}:
            points=p.parameters.get('points')
            if points is None:raise ValueError(p.id+': world-space points required')
            m.sweep(points,p.parameters.get('radius',min(p.size)/2));continue
        if p.kind not in supported:raise ValueError('No render adapter for '+p.kind)
        m.box(p.origin,p.size,2 if p.kind in {'window','curtain_panel'} else 0)
        if p.kind=='curtain_panel':
            x,y,z=p.origin;w,d,h=p.size
            if w>d:
                for i in [0,1,2,3]:m.box((x+w*i/3-.025,y-.025,z),(.05,d+.05,h),0)
            else:
                for i in [0,1,2,3]:m.box((x-.025,y+d*i/3-.025,z),(w+.05,.05,h),0)
    if previous is not None:m.face_owners.update({i:previous for i in range(start,len(m.faces))})
    from typed_interfaces import render_interfaces
    for raw in data['parts']:
        start=len(m.faces);render_interfaces(m,raw)
        m.face_owners.update({i:raw['id'] for i in range(start,len(m.faces))})
    used_names=set(m.face_owners.values())
    for index,connection in enumerate(data.get('connections',[])):
        start=len(m.faces)
        route=np.asarray(connection['route'],float);radius=connection['radius'];m.sweep(route,radius,32)
        if connection.get('fittings',False):
            for p,q in [(route[0],route[1]),(route[-1],route[-2])]:m.flange(p,q-p,radius)
        name=f'connection[{index}]'
        while name in used_names:name='@'+name
        used_names.add(name);m.connection_names[index]=name
        m.face_owners.update({i:name for i in range(start,len(m.faces))})
    if data.get('registered_geometry',False):
        from registered_geometry import seal
        seal(m)
    return m

class Renderer:
    def __init__(self,mesh,width=1200,height=1200,hatching=True,azimuth=45,elevation=None,pixel_ratio=1,shadows=False,projection='orthographic',finish='technical',camera_eye=None,camera_target=None,fov=50,near=.1,light_material_plan=None,allow_level=False,style_seed=0):
        from registered_geometry import assert_integrity
        assert_integrity(mesh)
        elevation=math.degrees(math.atan(.8/math.sqrt(2))) if elevation is None else elevation
        if not math.isfinite(azimuth) or not math.isfinite(elevation) or not (-90 if allow_level else 5)<=elevation<=90:raise ValueError('Camera elevation must be 5..90 degrees; use allow_level for explicit elevation views')
        if width<200 or height<200:raise ValueError('Render dimensions must be at least 200 pixels')
        if type(pixel_ratio)!=int or not 1<=pixel_ratio<=3:raise ValueError('pixel_ratio must be integer 1..3')
        self.pixel_ratio=pixel_ratio
        if type(style_seed)!=int or style_seed<0:raise ValueError('style_seed must be a nonnegative integer')
        self.style_seed=style_seed
        if finish not in {'technical','graphite'}:raise ValueError('Unknown drawing finish')
        self.finish=finish
        from visual_contract import LightMaterialPlan, _parse
        from dataclasses import asdict
        raw_light=light_material_plan if light_material_plan is not None else getattr(mesh,'light_material_plan',None)
        self.light_material_plan=asdict(_parse(LightMaterialPlan,raw_light)) if raw_light is not None else None
        from surface_mapping import mesh_maps
        self.surface_maps=mesh_maps(mesh,self.light_material_plan['materials']) if self.light_material_plan else {}
        self.light=np.asarray(self.light_material_plan['key_direction'] if self.light_material_plan else [-.6,.8,1.5],float)
        self.light/=np.linalg.norm(self.light)
        if projection not in {'orthographic','perspective'}:raise ValueError('Unknown projection')
        self.projection=projection
        self.shadows=shadows
        self.hatching=hatching
        self.w,self.h=width,height
        self.near_clip=None
        if camera_eye is not None or camera_target is not None:
            if camera_eye is None or camera_target is None or projection!='perspective':raise ValueError('Explicit eye and target require perspective together')
            eye=np.asarray(camera_eye,float);target=np.asarray(camera_target,float)
            if eye.shape!=(3,) or target.shape!=(3,) or not np.isfinite(eye).all() or not np.isfinite(target).all():raise ValueError('Camera eye/target need finite XYZ coordinates')
            if not math.isfinite(fov) or not 10<=fov<=120 or not math.isfinite(near) or near<=0:raise ValueError('Camera FOV must be 10..120 and near distance positive')
            view=eye-target;self.distance=float(np.linalg.norm(view))
            if self.distance<1e-8:raise ValueError('Camera eye and target coincide')
            view/=self.distance
            reference=np.array([0.,0.,1.]) if abs(view[2])<.999 else np.array([0.,1.,0.])
            right=np.cross(view,reference);right/=np.linalg.norm(right)
            self.basis=np.array([right,np.cross(right,view),view])
            self.eye=eye;self.target=target@self.basis.T;self.near_clip=near
            self.scale=height/(2*math.tan(math.radians(fov)/2));self.center=np.zeros(2)
        else:
            az,el=math.radians(azimuth),math.radians(elevation)
            right=np.array([math.sin(az),-math.cos(az),0])
            view=np.array([math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)])
            self.basis=np.array([right,np.cross(right,view),view])
            verts=np.array([p for face,_ in mesh.faces for p in face])@self.basis.T
            self.target=(verts.min(axis=0)+verts.max(axis=0))/2
            self.distance=float(np.linalg.norm(verts-self.target,axis=1).max())*2.5
            self.eye=(self.target+[0,0,self.distance])@self.basis
            screen=verts[:,:2] if projection=='orthographic' else (verts[:,:2]-self.target[:2])/(self.distance+self.target[2]-verts[:,2])[:,None]
            lo=screen.min(axis=0);hi=screen.max(axis=0)
            self.scale=min((width-140*pixel_ratio)/(hi[0]-lo[0]),(height-180*pixel_ratio)/(hi[1]-lo[1]))
            if self.scale<=0:raise ValueError('Canvas too small for scaled margins')
            self.center=(lo+hi)/2
        self.z=np.full((height,width),-np.inf)
        self.owner=np.zeros((height,width),dtype=np.int32)
        self.part_ids={name:i+1 for i,name in enumerate(sorted(set(mesh.face_owners.values())))}
        self.rgb=np.empty((height,width,3),dtype=np.uint8);self.rgb[:]=(247,246,242) if self.finish=='graphite' else (243,236,220)
    def project(self,p):
        q=np.asarray(p)@self.basis.T
        if self.projection=='perspective':
            distance=self.distance+self.target[2]-q[2]
            if distance<=0:raise ValueError('Point behind perspective camera')
            q=np.array([(q[0]-self.target[0])/distance,(q[1]-self.target[1])/distance,1/distance])
        return np.array([(q[0]-self.center[0])*self.scale+self.w/2,self.h/2-(q[1]-self.center[1])*self.scale,q[2]])
    def unproject(self,x,y,depth):
        qx=(np.asarray(x)-self.w/2)/self.scale+self.center[0]
        qy=(self.h/2-np.asarray(y))/self.scale+self.center[1]
        if self.projection=='perspective':
            distance=1/np.asarray(depth)
            qx=qx*distance+self.target[0];qy=qy*distance+self.target[1]
            depth=self.distance+self.target[2]-distance
        return np.stack((qx,qy,depth),axis=-1)@self.basis
    def triangle(self,p,color,world=None,owner=0,material=None,surface_map=None):
        a,b,c=p
        x0=max(0,int(np.floor(min(p[:,0]))));x1=min(self.w-1,int(np.ceil(max(p[:,0]))))
        y0=max(0,int(np.floor(min(p[:,1]))));y1=min(self.h-1,int(np.ceil(max(p[:,1]))))
        if x1<x0 or y1<y0:return
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-9:return
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
        z=u*a[2]+v*b[2]+w*c[2]
        target=self.z[y0:y1+1,x0:x1+1]
        mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(z>target+1e-9)
        target[mask]=z[mask];pixels=self.rgb[y0:y1+1,x0:x1+1];pixels[mask]=color
        self.owner[y0:y1+1,x0:x1+1][mask]=owner
        if self.hatching and world is not None:
            # Drawing-plane pencil strokes: straight hatching avoids the
            # sinusoidal bands caused by slicing cylinders with world planes.
            spacing=6*self.pixel_ratio
            phase=(xx+.65*yy)/spacing
            footprint=1.65/spacing
            def integral(t):return np.floor(t)*.12+np.minimum(np.mod(t,1),.12)
            coverage=(integral(phase+footprint/2)-integral(phase-footprint/2))/footprint
            strength=8+max(0,236-color[0])*.7
            if material is not None:
                normal=np.cross(world[1]-world[0],world[2]-world[0])
                surface=self.unproject(xx,yy,z)
                marks=surface_hatching(surface,material,normal,color,surface_map)
            elif self.finish=='graphite':
                normal=np.cross(world[1]-world[0],world[2]-world[0])
                marks=graphite_hatching(xx,yy,self.pixel_ratio,normal,color)
            else:marks=coverage*strength
            ink=np.asarray(color)-marks[...,None]
            pixels[mask]=np.clip(ink[mask],0,255).astype(np.uint8)
    def shadow_mask(self,mesh):
        # The shadow pass uses the same directional light as surface values.
        resolution=min(1200,max(400,self.w//self.pixel_ratio))
        azimuth=math.degrees(math.atan2(self.light[1],self.light[0]))
        elevation=math.degrees(math.asin(self.light[2]))
        lamp=Renderer(mesh,resolution,resolution,hatching=False,azimuth=azimuth,elevation=elevation,allow_level=True)
        for face,_ in mesh.faces:
            points=np.array([lamp.project(v) for v in face])
            for i in range(1,len(points)-1):lamp.triangle(points[[0,i,i+1]],(0,0,0))
        mask=np.zeros((self.h,self.w),dtype=bool)
        bias=2/lamp.scale
        for row in range(0,self.h,64):
            depth=self.z[row:row+64];yy,xx=np.where(np.isfinite(depth))
            if not len(xx):continue
            sy=yy+row
            world=self.unproject(xx+.5,sy+.5,depth[yy,xx]);lit=world@lamp.basis.T
            lx=np.floor((lit[:,0]-lamp.center[0])*lamp.scale+lamp.w/2).astype(int)
            ly=np.floor(lamp.h/2-(lit[:,1]-lamp.center[1])*lamp.scale).astype(int)
            inside=(lx>=0)&(lx<lamp.w)&(ly>=0)&(ly<lamp.h)
            ix,iy=lx[inside],ly[inside]
            # Conservative neighbouring samples reduce false self-shadow specks.
            surface=np.minimum.reduce([lamp.z[np.clip(iy+dy,0,lamp.h-1),np.clip(ix+dx,0,lamp.w-1)] for dx,dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]])
            mask[sy[inside],xx[inside]]=lit[inside,2]<surface-bias
        return mask

    def draw(self,mesh):
        from registered_geometry import assert_integrity
        assert_integrity(mesh)
        light=self.light
        for face_index,(face,tone) in enumerate(mesh.faces):
            n=np.cross(face[1]-face[0],face[2]-face[0]);n/=np.linalg.norm(n)
            name=mesh.face_owners.get(face_index)
            material=self.light_material_plan['materials'].get(name) if self.light_material_plan else None
            if self.light_material_plan:
                plan=self.light_material_plan
                base=material.get('base_value',232) if material else 232-tone*11
                shade=round(base*(plan['ambient']+plan['key_strength']*max(0,float(n@light))))
            else:
                shade=int(226+12*abs(n@light)-tone*11)
                if self.finish=='graphite':shade=round(244-(244-shade)*.68)
            if self.near_clip is not None:face=clip_polygon(face,self.eye,-self.basis[2],self.near_clip)
            if len(face)<3:continue
            ps=np.array([self.project(p) for p in face])
            owner=self.part_ids.get(mesh.face_owners.get(face_index),0)
            color=(shade,shade,shade) if self.light_material_plan else (shade,shade-1,shade-4) if self.finish=='graphite' else (shade,shade-5,shade-16)
            for i in range(1,len(ps)-1):self.triangle(ps[[0,i,i+1]],color,np.array(face)[[0,i,i+1]],owner,material,self.surface_maps.get(face_index))
        if self.shadows:
            shadow=self.shadow_mask(mesh)
            if self.finish=='graphite':
                soft=Image.fromarray(shadow.astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(2*self.pixel_ratio))
                amount=np.asarray(soft,dtype=float)/255*(self.light_material_plan['shadow_strength'] if self.light_material_plan else .12)
                amount[~np.isfinite(self.z)]=0
                self.rgb=np.clip(self.rgb.astype(float)*(1-amount[...,None]),0,255).astype(np.uint8)
            else:self.rgb[shadow]=np.clip(self.rgb[shadow].astype(float)*(1-self.light_material_plan['shadow_strength'] if self.light_material_plan else .84),0,255).astype(np.uint8)
        silhouettes=[]
        valid_depth=self.z[np.isfinite(self.z)]
        depth_range=(float(valid_depth.min()),float(valid_depth.max())) if len(valid_depth) else (0,1)
        for a,b,n1,n2 in mesh.smooth_edges:
            sight=self.basis[2] if self.projection=='orthographic' else self.eye-(a+b)/2
            if (n1@sight)*(n2@sight)<=0:silhouettes.append((a,b))
        for edge_index,(a,b) in enumerate(mesh.edges+silhouettes):
            weight=self.pixel_ratio;ink_adjust=0
            if self.light_material_plan:
                role=0 if edge_index>=len(mesh.edges) else 2 if edge_index in getattr(mesh,'detail_edge_indices',set()) else 1
                weight=max(1,round(self.pixel_ratio*self.light_material_plan['line_weights'][role]))
                ink_adjust=(-14,0,24)[role]
            if self.near_clip is not None:
                clipped=clip_segment(a,b,self.eye,-self.basis[2],self.near_clip)
                if clipped is None:continue
                a,b=clipped
            clipped=clip_screen_line(self.project(a),self.project(b),self.w,self.h)
            if clipped is None:continue
            a,b=clipped;count=max(2,int(np.linalg.norm(b[:2]-a[:2])*2))
            ps=np.linspace(a,b,count);x=np.floor(ps[:,0]).astype(int);y=np.floor(ps[:,1]).astype(int)
            ok=(x>=0)&(x<self.w)&(y>=0)&(y<self.h);x,y,z=x[ok],y[ok],ps[ok,2]
            # Conservative one-raster-pixel footprint at tangent boundaries.
            # Centre-only depth can self-occlude silhouettes at subpixel offsets.
            local_depth=np.minimum.reduce([self.z[np.clip(y+oy,0,self.h-1),np.clip(x+ox,0,self.w-1)] for ox,oy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]])
            for dx in range(-(weight//2),weight-weight//2):
                for dy in range(-(weight//2),weight-weight//2):
                    sx,sy=x+dx,y+dy
                    inside=(sx>=0)&(sx<self.w)&(sy>=0)&(sy<self.h)
                    sx,sy,sz=sx[inside],sy[inside],z[inside]
                    bias=.05/self.scale/(self.distance if self.projection=='perspective' else 1)
                    visible=sz>=local_depth[inside]-bias
                    if self.finish=='graphite':
                        vx,vy=sx[visible],sy[visible]
                        self.rgb[vy,vx]=np.clip(contour_ink(vx,vy,self.z[vy,vx],depth_range,self.pixel_ratio).astype(int)+ink_adjust,0,255).astype(np.uint8)
                    else:self.rgb[sy[visible],sx[visible]]=(86,80,68)
        if self.finish=='graphite':return Image.fromarray(finish_paper(self.rgb,self.pixel_ratio,self.style_seed))
        # Seeded subtle grain, identical for repeat builds.
        noise=np.random.default_rng(41+self.style_seed).integers(-2,3,(self.h,self.w,1))
        return Image.fromarray(np.clip(self.rgb.astype(np.int16)+noise,0,255).astype(np.uint8))

    def component_visibility(self,data):
        """Depth-tested surface coverage after draw; not recognizability.

        Counts are at the internal raster resolution before downsampling.
        A zero cannot distinguish occlusion, cropping and undersampling.
        """
        counts=np.bincount(self.owner.ravel(),minlength=len(self.part_ids)+1)
        records=[];by_kind={}
        for part in data['parts']:
            name=part['id'];kind=part['kind']
            if name not in self.part_ids:raise ValueError('Missing component ownership: '+name)
            count=int(counts[self.part_ids[name]])
            records.append({'id':name,'kind':kind,'visible_pixels':count})
            group=by_kind.setdefault(kind,{'total':0,'with_visible_surface':0,'without_visible_surface':0})
            group['total']+=1
            group['with_visible_surface' if count else 'without_visible_surface']+=1
        return {'components':records,'by_kind':by_kind}

    def connection_visibility(self,mesh,data):
        """Observed route pixels, not proof of topology or endpoint attachment."""
        report=[]
        for index,link in enumerate(data.get('connections',[])):
            name=mesh.connection_names[index]
            visible=self.owner==self.part_ids[name]
            endpoint_counts=[]
            for point in [link['route'][0],link['route'][-1]]:
                point=np.asarray(point,float)
                if self.near_clip is not None and (point-self.eye)@(-self.basis[2])<self.near_clip:
                    endpoint_counts.append(0);continue
                screen=self.project(point)
                # Search the projected fitting footprint, not an arbitrary fixed
                # pixel radius. Perspective scales the two endpoints separately.
                extent=max(np.linalg.norm(self.project(point+axis*link['radius']*1.8)[:2]-screen[:2]) for axis in self.basis[:2])
                radius=max(2.,extent+1.)
                x,y=screen[:2]
                x0=max(0,int(math.floor(x-radius)));x1=min(self.w,int(math.ceil(x+radius))+1)
                y0=max(0,int(math.floor(y-radius)));y1=min(self.h,int(math.ceil(y+radius))+1)
                if x1<=x0 or y1<=y0:endpoint_counts.append(0);continue
                yy,xx=np.mgrid[y0:y1,x0:x1]
                nearby=(xx+.5-x)**2+(yy+.5-y)**2<=radius**2
                endpoint_counts.append(int(np.count_nonzero(visible[y0:y1,x0:x1]&nearby)))
            report.append({'index':index,'from':link['from'],'to':link['to'],
                           'visible_pixels':int(visible.sum()),
                           'endpoint_neighborhood_pixels':endpoint_counts})
        return report

    def label(self,im,labels):
        """Anchor each leader to a depth-tested pixel belonging to its target."""
        output=im.copy();d=ImageDraw.Draw(output);font=ImageFont.load_default(size=18*self.pixel_ratio)
        boxes=[];report=[]
        for item in labels:
            name=item['target'];text=item['text'];position=item['position']
            if name not in self.part_ids:raise ValueError('Unknown label target: '+name)
            if not isinstance(text,str) or not text.strip() or any(ord(c)<32 for c in text):raise ValueError('Label text must be one nonempty line')
            if len(position)!=2 or any(not math.isfinite(v) or not 0<=v<=1 for v in position):raise ValueError('Label position must be normalized XY')
            yy,xx=np.where(self.owner==self.part_ids[name])
            if len(xx)<4:raise ValueError('Label target not sufficiently visible: '+name)
            # Select a real visible pixel nearest the visible region centroid.
            best=np.argmin((xx-xx.mean())**2+(yy-yy.mean())**2);anchor=(int(xx[best]),int(yy[best]))
            px,py=int(position[0]*self.w),int(position[1]*self.h)
            box=d.textbbox((px,py),text,font=font);x0,y0,x1,y1=box
            if x0<0 or y0<0 or x1>=self.w or y1>=self.h:raise ValueError('Label outside image: '+name)
            if any(x0<b[2]+6 and x1+6>b[0] and y0<b[3]+6 and y1+6>b[1] for b in boxes):raise ValueError('Overlapping labels')
            if np.isfinite(self.z[y0:y1+1,x0:x1+1]).any():raise ValueError('Label text overlaps geometry: '+name)
            boxes.append(box)
            start=(max(x0,min(anchor[0],x1)),y1+3)
            d.line([start,anchor],fill=(70,64,53),width=self.pixel_ratio)
            ax,ay=anchor;dot=2*self.pixel_ratio;d.ellipse((ax-dot,ay-dot,ax+dot,ay+dot),fill=(70,64,53))
            d.text((px,py),text,font=font,fill=(70,64,53))
            report.append({'target':name,'anchor':list(anchor),'text':text})
        return output,report

def main():
    p=argparse.ArgumentParser();p.add_argument('--scene');p.add_argument('--floors',type=int,default=12);p.add_argument('--out',required=True);p.add_argument('--width',type=int,default=1400);p.add_argument('--height',type=int,default=1600)
    p.add_argument('--azimuth',type=float,default=45);p.add_argument('--elevation',type=float);p.add_argument('--title',default='ARCHITECTURAL STUDY')
    p.add_argument('--supersample',type=int,choices=[1,2,3],default=2)
    p.add_argument('--no-shadows',action='store_true')
    p.add_argument('--finish',choices=['technical','graphite'],default='technical')
    p.add_argument('--projection',choices=['orthographic','perspective'],default='orthographic')
    p.add_argument('--eye',nargs=3,type=float);p.add_argument('--target',nargs=3,type=float)
    p.add_argument('--fov',type=float,default=50);p.add_argument('--near',type=float,default=.1)
    a=p.parse_args();data=json.loads(Path(a.scene).read_text()) if a.scene else tower(a.floors,3)
    ss=a.supersample
    m=build(data);r=Renderer(m,a.width*ss,a.height*ss,azimuth=a.azimuth,elevation=a.elevation,pixel_ratio=ss,shadows=not a.no_shadows,projection=a.projection,finish=a.finish,camera_eye=a.eye,camera_target=a.target,fov=a.fov,near=a.near);im=r.draw(m)
    im,labels=r.label(im,data.get('labels',[]))
    if a.title:
        d=ImageDraw.Draw(im);d.text((55*ss,20*ss),a.title,fill=(80,72,60),font=ImageFont.load_default(size=18*ss))
    if ss>1:im=im.resize((a.width,a.height),Image.Resampling.LANCZOS)
    for label in labels:label['anchor']=[v/ss for v in label['anchor']]
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);im.save(a.out)
    print(json.dumps({'parts':len(data['parts']),'faces':len(m.faces),'edges':len(m.edges),'labels':labels,'connections':r.connection_visibility(m,data),'component_visibility':r.component_visibility(data),'visibility_raster_size':[r.w,r.h],'output':a.out}))
if __name__=='__main__':main()
