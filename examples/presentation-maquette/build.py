"""Standalone construction example. Prints specification; does not bundle source imagery."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from maquette_parts import *
def specification():
 s=dict(schema_version=2,title='Pabellón botánico',camera_notes='Front-left oblique; dimensions and unseen rear inferred',limitations=['Maqueta conceptual; espesores y caras ocultas inferidos. Vegetación simplificada.'],components=[],assemblies=[],correspondence=[],presentation={'direction':[-1,-1.5,1],'zoom':1.3})
 def add(name,shapes,color,host=None,opacity=1):
  host=host or name
  s['components'].append(dict(id=name,shapes=shapes,color=color,opacity=opacity,provenance='observed',evidence='Visible feature in reference; dimensions inferred',hidden_assumptions='Hidden depth and exact dimensions inferred',support_note='Mounted to '+host))
  g=next((g for g in s['assemblies'] if g['id']==host),None)
  if g is None:
   g=dict(id=host,label=host,members=[],offset=[0,0,0] if host=='site' else [0,0,2],fixed=host=='site',provenance='observed',evidence='Source-visible family',separation_note='Conceptual assembly separation');s['assemblies'].append(g)
  g['members'].append(name);s['correspondence'].append(dict(parts=[name],image_bbox=[0,0,1,1],evidence='Actual source comparison required'))
 add('site',[box([-3,-4,-.2],[17,19,.2])],'#d6d2c8')
 add('plinth',wall_openings(8,.7,.2,[(3,0,2,.7)])+[box([0,.2,0],[.2,11.8,.7]),box([7.8,.2,0],[.2,11.8,.7]),box([0,11.8,0],[8,.2,.7])],'#c7c0af','building')
 frames=[];glass=[]
 for x,w in ((.2,2.8),(5,2.8)):
  win=window(w,2.5,3,3);frames+=translated(win['frame'],[x,0,.7]);glass+=translated(win['glass'],[x,0,.7])
 # Door opening and transom, one open leaf to show actual access.
 for x in (3,5):frames.append(box([x,-.04,0],[.055,.1,3.2]))
 frames.append(box([3,-.04,2.4],[2,.1,.06]));win=window(2,.7,2,1);frames+=translated(win['frame'],[3,0,2.5]);glass+=translated(win['glass'],[3,0,2.5])
 for x in (3,4.95):
  frames += [box([x,-.85,0],[.05,.85,.05]),box([x,-.85,2.4],[.05,.85,.05]),box([x,-.85,0],[.05,.05,2.4])];glass.append(box([x+.015,-.8,.05],[.012,.75,2.3]))
 for side in (0,8):
  win=window(11.6,2.5,12,3)
  for role,shapes in win.items():
   for q in shapes:q['rotation']=[0,0,90];q['at']=[side,.2,.7] if 'at' not in q else [side-q['at'][1],.2+q['at'][0],.7+q['at'][2]]
   (frames if role=='frame' else glass).extend(shapes)
 for y in (0,12):
  glass.append({'type':'mesh','vertices':[[.1,y,3.2],[7.9,y,3.2],[4,y,5.2]],'faces':[[0,1,2]]})
  for i in range(1,16):
   x=i*.5;top=5.2-abs(x-4)*.5;frames.append(rod([x,y,3.2],[x,y,top],.035))
 add('wall_frames',frames,'#657675','building');add('wall_glass',glass,'#c0d8d9','building',.25)
 roof=pitched_roof(8,12,3.2,2,12)
 for role,shapes in roof.items():add('roof_'+role,shapes,'#b7ced0' if role=='skin' else '#637675','roof',.24 if role=='skin' else 1)
 vents=[]
 for y in [i*.5 for i in range(24)]:vents.append(box([3.65,y,5.22],[.7,.035,.28]))
 vents += [box([3.55,0,5.5],[.9,12,.08])]
 add('ridge_vent',vents,'#718383','roof')
 add('annex',translated(wall_openings(3,3,.2,[(1.3,0,.9,2.1)]),[8,0,0])+[box([10.8,.2,0],[.2,6.8,3]),box([8,6.8,0],[3,.2,3]),box([8,0,3],[3,7,.16])],'#d1cabc','annex')
 services=[box([8.6,2,3.16],[1.2,1,.6]),box([9,4,3.16],[.6,.8,.4])]
 for z in [3.25+i*.08 for i in range(6)]:services.append(box([8.55,1.96,z],[1.3,.03,.025]))
 services += [rod([9.2,2.5,3.76],[9.2,1.3,3.76],.12),rod([9.2,1.3,3.76],[9.2,1.3,3.16],.12)]
 services += [box([9.3,-.015,0],[.9,.08,2.1])]
 add('roof_services',services,'#9ca6a1','annex')
 beds=[];plants=[]
 for x in (.55,5.3):
  for y in (1,4,7,10):
   beds.append(box([x,y,0],[2.1,1.6,.45]))
   for j in range(6):
    xx=x+.3+(j%3)*.65;yy=y+.3+(j//3)*.8
    plants += [rod([xx,yy,.45],[xx,yy,1.2],.025),{'type':'ellipsoid','at':[xx,yy,.9],'radii':[.22,.22,.35],'segments':10,'rows':6}]
 add('beds',beds,'#c7c2b2','interior');add('planting',plants,'#7d9a6b','interior')
 bench=[];metal=[];trees=[]
 for x,y in ((-1.3,2),(-1.3,7),(9,-2)):
  for i in range(4):bench.append(box([x,y+i*.12,.48],[1.5,.08,.06]))
  bench.append(box([x,y+.42,.6],[1.5,.06,.4]))
  for dx in (.1,1.3):metal.append(box([x+dx,y+.08,0],[.07,.3,.48]))
 for x,y in ((-2,10),(12,-2)):
  metal.append(rod([x,y,0],[x,y,2.6],.09))
  for dx,dy,z in ((0,0,3),(.35,.2,3.35),(-.3,.1,2.9)):
   trees.append({'type':'ellipsoid','at':[x+dx,y+dy,z],'radii':[.7,.7,.8],'segments':12,'rows':8})
 add('benches',bench,'#a78d69','site');add('fittings',metal,'#68756c','site');add('trees',trees,'#92a77f','site')
 drain=[]
 for x in (0,8):
  drain += [rod([x,0,3.2],[x,12,3.2],.055),rod([x,0,3.2],[x,0,0],.045)]
 for y in (2,4,6,8,10):drain.append(rod([0,y,.7],[0,y,3.2],.04))
 add('gutters',drain,'#71817d','building')
 shade=[quad([[2.8,-.8,2.8],[5.2,-.8,2.8],[5.2,0,3],[2.8,0,3]])]
 add('entrance_canopy',shade,'#aec7c9','building',.4)
 features=[]
 for ident,level,ids in [('enclosure','primary',['plinth','annex']),('roof','primary',['roof_skin']),('glazing','secondary',['wall_glass','wall_frames']),('roof_frame','secondary',['roof_structure']),('roof_detail','fine',['roof_seams','ridge_vent','roof_services']),('interior','fine',['beds','planting']),('landscape','secondary',['benches','trees'])]:
  features.append(dict(id=ident,level=level,parts=ids,evidence='Visible '+ident,status='modeled',critical=ident!='landscape'))
 s['quality_contract']=dict(features=features,detail_zones=[dict(id='facade',features=['enclosure','glazing','interior']),dict(id='roof',features=['roof','roof_frame','roof_detail'])],landmarks=['enclosure','roof','glazing'],access_scope='Entrance to central path',protected_spaces=[dict(id='door',purpose='Entrance opening',min=[3.1,-.1,.02],max=[4.9,.2,2.3]),dict(id='aisle',purpose='Central path',min=[3.1,.3,.02],max=[4.9,11.5,2.3])],overlap_review=[])
 s['access_network']=dict(entry='outside',targets=['inside'],nodes=[dict(id='outside',point=[4,-2,0]),dict(id='inside',point=[4,11,0])],links=[{'from':'outside','to':'inside','supports':['site']}])
 return s
if __name__=='__main__':print(json.dumps(specification(),ensure_ascii=False))
