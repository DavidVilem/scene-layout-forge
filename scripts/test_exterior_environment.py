import copy
import json
import tempfile
import unittest
from pathlib import Path

from urban_skyline import scene
from scene_model import validate
from finish_contract import preflight,freeze,request,compile_handoff
from exterior_environment import errors
from pixel_review import requirements


class ExteriorEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=scene(16,'avenue',True)
    def fresh(self):return copy.deepcopy(self.base)
    def part(self,s,key):return next(p for p in s['parts'] if p['id']==key)

    def test_current_exterior_scope_passes_without_hidden_rooms(self):
        self.assertEqual(preflight(self.base),[])
        self.assertNotIn('architecture_contract',self.base)
        self.assertNotIn('materialized_design',self.base)
        self.assertIn('load capacity',self.base['exterior_environment']['unverified'])
    def test_floating_roof_equipment_still_fails(self):
        s=self.fresh();self.part(s,'terraced-penthouse')['origin'][2]+=.4
        self.assertTrue(validate(s))
    def test_missing_support_still_fails(self):
        s=self.fresh();s['bearings']=[b for b in s['bearings'] if b['part']!='terraced-body-1']
        self.assertTrue(validate(s))
    def test_partial_overhang_cannot_pass_as_bearing(self):
        s=self.fresh();self.part(s,'terraced-body-1')['origin'][0]+=10
        self.assertTrue(any('overhang' in e for e in errors(s)))
    def test_street_through_envelope_rejected(self):
        s=self.fresh();p=self.part(s,'terraced-body-0');p['origin'][:2]=[35,30]
        self.assertTrue(any('street crosses' in e for e in errors(s)))
    def test_disconnected_street_rejected(self):
        s=self.fresh();self.part(s,'cross-7')['origin'][1]+=8
        self.assertTrue(any('disconnected' in e for e in errors(s)))
    def test_interior_cannot_claim_exterior_scope(self):
        for field,value in [('architecture_contract',{}),('room_programs',{'office':{}}),('representation',{'type':'cutaway'})]:
            s=self.fresh();s[field]=value;self.assertTrue(preflight(s))
        s=self.fresh();s['visual_plan']['view_intent']='interior';self.assertTrue(preflight(s))
    def test_old_graph_scene_cannot_add_exterior_bypass(self):
        s=self.fresh();s['design_intent']={'domain':'building'};self.assertTrue(errors(s))
    def test_unregistered_parts_and_hidden_scope_fail(self):
        s=self.fresh();s['exterior_environment']['roles'].pop('roof-equipment');self.assertTrue(errors(s))
        s=self.fresh();s['exterior_environment']['unverified']=[];self.assertTrue(errors(s))
    def test_malformed_scope_reports_error(self):
        for field in ('unverified','roles','alternatives','focal','envelopes','roads'):
            s=self.fresh();s['exterior_environment'][field]=False;self.assertTrue(errors(s))
        for value in (None,{},False,[]):
            s=self.fresh();s['exterior_environment']=value;self.assertTrue(preflight(s))
    def test_explicit_annotations_only(self):
        a=scene(16,'avenue');b=scene(16,'avenue',True)
        self.assertEqual(a['parts'],b['parts']);self.assertEqual(a['callouts'],[])
        self.assertEqual(len(b['callouts']),5)
    def test_diverse_spatial_organizations_remain_valid(self):
        layouts=[]
        for i,family in enumerate(('avenue','staggered','courtyard')):
            s=scene(20+i,family);self.assertEqual(preflight(s),[])
            layouts.append([(p['origin'],p['size']) for p in s['parts'] if p.get('semantic_role')=='exterior building envelope'])
        self.assertEqual(len({json.dumps(x) for x in layouts}),3)
    def test_camera_override_is_not_discarded(self):
        camera=dict(projection='orthographic',azimuth=25,elevation=45)
        self.assertEqual(scene(16,camera=camera)['camera'],camera)
    def test_annotations_can_use_middle_sky_and_nested_roof_destination(self):
        import numpy as np
        from types import SimpleNamespace
        from annotation_plan import create,errors as annotation_errors
        owner=np.ones((300,500),dtype=int)
        owner[:80,100:400]=0  # side margins are fully occupied
        owner[160:200,200:240]=2  # garden surrounded by another annotated roof
        renderer=SimpleNamespace(owner=owner,part_ids={'roof':1,'garden':2},w=500,h=300)
        s={'parts':[{'id':'roof','kind':'wall'},{'id':'garden','kind':'slab'}],
           'callouts':[dict(id='r',target='roof',text='ROOF'),dict(id='g',target='garden',text='GARDEN')]}
        notes=create(s,renderer)
        self.assertEqual(annotation_errors(notes,renderer),[])
        self.assertEqual(len(notes),2)
        for note in notes:
            self.assertGreaterEqual(note['text_box'][0],.2)
            self.assertLessEqual(note['text_box'][2],.8)
    def test_facade_bands_wrap_all_sides_at_same_heights(self):
        import numpy as np
        from render_scene import build
        from scene_model import make_part
        mesh=build({'units':'m','parts':[make_part('mass','wall',[0,0,0],[8,10,12],
                   parameters={'panel_size':[2,3],'panel_faces':'all'})]})
        for z in (3,6,9):
            bands=[(a,b) for a,b in mesh.edges if abs(a[2]-z)<1e-6 and abs(b[2]-z)<1e-6]
            self.assertEqual(len(bands),4)
            self.assertTrue(all(np.linalg.norm(a-b)>0 for a,b in bands))
    def test_actual_guide_freeze_and_persistent_request(self):
        from render_scene import build,Renderer
        from view_contract import create
        from execution_history import preserve,errors as history_errors
        from history_run import new_run
        s=self.fresh()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);brief='Draw a city from a roof with five English annotations.'
            run=new_run(root,'urban-regression',brief)
            mesh=build(s);renderer=Renderer(mesh,1536,1024,hatching=False,**s['camera'])
            guide=run/'07-representation/guide.png';renderer.draw(mesh).save(guide)
            view=create(s,s,renderer,guide);lock=freeze(s,view)
            self.assertEqual(len(view['annotations']),5)
            self.assertIn('exterior_scope',compile_handoff(lock))
            self.assertIn('exterior:setbacks',requirements(lock))
            prompt=request(lock,brief,'Neutral graphite and rich constructed detail on near-white paper.')
            attempt=preserve(lock,run,guide,brief,prompt,sources=[Path(__file__).with_name('urban_skyline.py')])
            self.assertEqual(history_errors(lock,run),[])
            self.assertTrue((attempt/'tool-request.json').exists())
            stale=self.fresh();self.part(stale,'terraced-body-0')['size'][2]+=.1
            with self.assertRaises(ValueError):freeze(stale,view)


if __name__=='__main__':unittest.main()
