"""Depth-owned annotation tips, exact text, boxes and routed guide leaders.

Routing is a bounded orthogonal search, not a general typography engine. If no
clear route exists it fails and asks for a new placement/view, never a fake tip.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import heapq
import numpy as np


def signature(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class AnnotationPlan:
    id: str
    text: str
    target: str
    tip_xy: list
    text_box: list
    leader: list
    visible_guide_pixels: int
    surface_owner: str

    def __post_init__(self):
        for name in ('id', 'text', 'target', 'surface_owner'):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip(): raise ValueError('annotation ' + name + ' required')
        if any(ord(c) < 32 for c in self.text): raise ValueError('annotation text must be a single line')
        for point in [self.tip_xy] + self.leader:
            if not isinstance(point, list) or len(point) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 < v < 1 for v in point):
                raise ValueError('annotation route points must be inside the raster')
        if len(self.leader) < 2 or self.leader[-1] != self.tip_xy: raise ValueError('leader must end at owned tip')
        if len(self.text_box) != 4 or not 0 < self.text_box[0] < self.text_box[2] < 1 or not 0 < self.text_box[1] < self.text_box[3] < 1:
            raise ValueError('annotation text box must be inside the raster')
        if self.visible_guide_pixels < 9 or self.surface_owner != self.target: raise ValueError('annotation lacks owned visible surface')


def _samples(path, width, height):
    pixels = []
    for a, b in zip(path, path[1:]):
        a, b = np.asarray(a)*[width, height], np.asarray(b)*[width, height]
        q = np.linspace(a, b, max(2, int(np.linalg.norm(b-a)*2)+1))
        pixels.extend(q.astype(int))
    return np.asarray(pixels, int)


def _box_mask(box, width, height, padding=1):
    x0, y0, x1, y1 = box
    return (max(0, math.floor(x0*width)-padding), max(0, math.floor(y0*height)-padding),
            min(width, math.ceil(x1*width)+padding), min(height, math.ceil(y1*height)+padding))


def route_clear(path, renderer, blocked):
    pts = _samples(path, renderer.w, renderer.h)
    if not len(pts) or np.any(pts < 0) or np.any(pts[:, 0] >= renderer.w) or np.any(pts[:, 1] >= renderer.h): return False
    return not bool(blocked[pts[:, 1], pts[:, 0]].any())


def _route_around(start, tip, renderer, blocked):
    """Bounded raster A* fallback; every compressed segment is rechecked."""
    w,h=renderer.w,renderer.h
    source=(int(start[0]*w),int(start[1]*h));goal=(int(tip[0]*w),int(tip[1]*h))
    if any(not 0<=p[0]<w or not 0<=p[1]<h or blocked[p[1],p[0]] for p in (source,goal)):return None
    # Four-neighbor traversal cannot jump across a one-pixel protected contour.
    queue=[(abs(source[0]-goal[0])+abs(source[1]-goal[1]),0,source)]
    parent={source:None};cost={source:0};expanded=0
    while queue and expanded<min(w*h,200000):
        _,distance,point=heapq.heappop(queue)
        if distance!=cost.get(point):continue
        if point==goal:
            points=[]
            while point is not None:
                points.append([(point[0]+.5)/w,(point[1]+.5)/h]);point=parent[point]
            points.reverse();points[0]=start;points[-1]=tip
            # Greedy line-of-sight simplification preserves exact mask avoidance.
            path=[points[0]];index=0
            while index<len(points)-1:
                next_index=len(points)-1
                while next_index>index+1 and not route_clear([points[index],points[next_index]],renderer,blocked):next_index-=1
                path.append(points[next_index]);index=next_index
            return path if route_clear(path,renderer,blocked) else None
        expanded+=1
        x,y=point
        for candidate in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            nx,ny=candidate
            if nx<1 or ny<1 or nx>=w-1 or ny>=h-1 or blocked[ny,nx]:continue
            new=distance+1
            if new>=cost.get(candidate,float('inf')):continue
            cost[candidate]=new;parent[candidate]=point
            heapq.heappush(queue,(new+abs(nx-goal[0])+abs(ny-goal[1]),new,candidate))
    return None


def create(scene, renderer):
    labels = scene.get('callouts', [])
    if len({c['id'] for c in labels}) != len(labels): raise ValueError('duplicate annotation IDs')
    width, height = renderer.w, renderer.h
    # Allocate scarce label margins in target order; a bottom-floor note must
    # not claim the only top slot and create a barrier across every later note.
    def target_order(label):
        yy,xx=np.where(renderer.owner==renderer.part_ids.get(label['target'],-1))
        return (float(yy.mean()) if len(yy) else float('inf'),float(xx.mean()) if len(xx) else 0,label['id'])
    labels=sorted(labels,key=target_order)
    protected = set(scene.get('context_plan', {}).get('protected_ids', []))
    protected.update(p['id'] for p in scene.get('parts', []) if p.get('kind') in {'person', 'worker'})
    protected.update(key for j in scene.get('camera_junctions', []) if j.get('required', True) for key in j['owners'])
    placed = []
    for index, label in enumerate(labels):
        target = label['target']
        if target not in renderer.part_ids: raise ValueError('callout target absent from display: ' + target)
        mask = renderer.owner == renderer.part_ids[target]
        count = int(mask.sum())
        if count < 9: raise ValueError('callout target lacks readable guide surface: ' + target)
        # Erosion excludes contour ambiguity without losing thin, useful targets.
        inner = mask.copy()
        for _ in range(max(1, round(min(width, height)/256))):
            pad = np.pad(inner, 1)
            next_mask = inner & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
            if next_mask.sum() < 4: break
            inner = next_mask
        yy, xx = np.where(inner)
        centroid = int(np.argmin((xx-xx.mean())**2+(yy-yy.mean())**2))
        tip = [(float(xx[centroid])+.5)/width, (float(yy[centroid])+.5)/height]
        # Font dimensions scale with usage size, independent of supersampling.
        tw = max(.035, len(label['text'])*.0075 + .012); th = .022
        options = []
        if label.get('position'): options.append(label['position'])
        for row in range(max(5, len(labels)+1)):
            y = .035 + row*.045
            options.extend([[.025, y], [max(.025, .975-tw), y], [.025, .965-y-th], [max(.025, .975-tw), .965-y-th]])
        # Full skyline compositions may fill both side margins while leaving
        # open sky in the middle. Search actual empty pixels there as well.
        for y in np.arange(.025,.97-th,.045):
            for x in np.arange(.025,.97-tw,.055):options.append([float(x),float(y)])
        pinned=1 if label.get('position') else 0
        options=options[:pinned]+sorted(options[pinned:],key=lambda xy:math.dist([xy[0]+tw/2,xy[1]+th/2],tip))
        box = None
        for x, y in options:
            candidate = [x, y, x+tw, y+th]
            if not 0 < x < x+tw < 1 or not 0 < y < y+th < 1: continue
            if any(x < b[2]+.006 and x+tw+.006 > b[0] and y < b[3]+.006 and y+th+.006 > b[1] for b in [p['text_box'] for p in placed]): continue
            x0, y0, x1, y1 = _box_mask(candidate, width, height, 0)
            if np.any(renderer.owner[y0:y1, x0:x1] != 0): continue
            box = candidate; break
        if box is None: raise ValueError('no empty annotation text placement: ' + label['id'])
        placed.append({'id': label['id'], 'text': label['text'], 'target': target, 'tip_xy': tip,
                       'text_box': box, 'visible_guide_pixels': count, 'surface_owner': target})
    occupied = np.zeros((height, width), bool)
    for record in placed:
        blocked = occupied.copy()
        # A destination on a large roof must not turn the whole roof into an
        # impenetrable wall around a second note (e.g. a planted terrace).
        # Protect the actual destination neighborhoods, not all pixels owned by
        # another annotated building. People and critical interfaces stay whole.
        for name in protected - {record['target']}:
            if name in renderer.part_ids: blocked |= renderer.owner == renderer.part_ids[name]
        for other in placed:
            if other is record: continue
            tx,ty=other['tip_xy'];rr=max(3,round(min(width,height)*.006))
            cx,cy=int(tx*width),int(ty*height)
            blocked[max(0,cy-rr):min(height,cy+rr+1),max(0,cx-rr):min(width,cx+rr+1)]=True
            x0, y0, x1, y1 = _box_mask(other['text_box'], width, height)
            blocked[y0:y1, x0:x1] = True
        x0, y0, x1, y1 = record['text_box']; tip = record['tip_xy']
        starts = [[(x0+x1)/2, y1+.004], [x1+.004, (y0+y1)/2], [x0-.004, (y0+y1)/2]]
        routes = []
        for start in starts:
            routes.extend([[start, tip], [start, [tip[0], start[1]], tip], [start, [start[0], tip[1]], tip]])
            for lane in [.015, .985]:
                routes.extend([[start, [lane, start[1]], [lane, tip[1]], tip],
                               [start, [start[0], lane], [tip[0], lane], tip]])
        valid = [path for path in routes if route_clear(path, renderer, blocked)]
        if not valid:
            for start in starts:
                path=_route_around(start,tip,renderer,blocked)
                if path is not None:valid.append(path);break
        if not valid: raise ValueError('no clear leader avoiding people, interfaces and labels: ' + record['id'])
        record['leader'] = min(valid, key=lambda p: sum(math.dist(a, b) for a,b in zip(p, p[1:])))
        item = AnnotationPlan(**record)
        pts = _samples(item.leader, width, height)
        occupied[pts[:, 1], pts[:, 0]] = True
    return placed


def errors(records, renderer=None):
    issues = []
    for raw in records:
        try:
            item = AnnotationPlan(**raw)
            if renderer is not None:
                x, y = item.tip_xy
                if renderer.owner[int(y*renderer.h), int(x*renderer.w)] != renderer.part_ids.get(item.target, -1):
                    issues.append('annotation tip is on another component: ' + item.id)
        except (ValueError, TypeError, KeyError) as exc: issues.append(str(exc))
    return issues
