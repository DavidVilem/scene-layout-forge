import copy,tempfile,unittest
from pathlib import Path
from PIL import Image
from finish_contract import freeze,compile_handoff,digest,preflight,request
from render_scene import build,Renderer
from view_contract import create


class FinishV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.guide=Path(cls.temp.name)/'guide.png'
        cls.scene={'units':'m','workflow_version':3,'parts':[{'id':'plate','kind':'slab','origin':[0,0,0],'size':[2,2,.2]}],
            'connections':[],'expected_counts':{'slab':1},'delivery_counts':{'slab':1},'callouts':[],
            'detail_regions':[{'name':'foundation','primary':['plate'],'secondary':[],'quiet_reason':'exposed unadorned slab','microdetails':'edge joints'}],
            'visual_plan':{'objective':'Read the supported slab','primary':['plate'],'readable':['plate']},
            'context_plan':{'mode':'isolated'},
            'detail_budget':{'regions':[{'name':'foundation','primary':['plate'],'secondary':[],'quietReason':'exposed unadorned slab','quiet_kind':'unadorned_surface'}]},
            'light_material_plan':{'materials':{'plate':{'family':'concrete'}}},
            'camera':{'projection':'perspective','eye':[5,-6,5],'target':[1,1,0],'fov':45}}
        mesh=build(cls.scene);r=Renderer(mesh,320,240,projection='perspective',camera_eye=[5,-6,5],camera_target=[1,1,0],fov=45)
        r.draw(mesh).save(cls.guide);cls.view=create(cls.scene,cls.scene,r,cls.guide)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_valid_actual_raster_gates_pass(self):
        lock=freeze(self.scene,self.view);self.assertEqual(lock['visual_contract']['guide_status'],'passed')
    def test_hidden_focus_cannot_freeze_even_with_recomputed_digest(self):
        view=copy.deepcopy(self.view);view['projection_review']['components']['plate']['visible_pixels']=0
        view['projection_review_sha256']=digest(view['projection_review'])
        with self.assertRaisesRegex(ValueError,'usable guide surface'):freeze(self.scene,view)
    def test_missing_projection_cannot_freeze(self):
        view=copy.deepcopy(self.view);view.pop('projection_review')
        with self.assertRaisesRegex(ValueError,'projection review'):freeze(self.scene,view)
    def test_v1_downgrade_cannot_freeze_v3(self):
        view=copy.deepcopy(self.view);view['version']=1
        with self.assertRaisesRegex(ValueError,'bound v2'):freeze(self.scene,view)
    def test_all_four_plans_required(self):
        changed=copy.deepcopy(self.scene);changed.pop('context_plan')
        self.assertTrue(any('explicit visual' in e for e in preflight(changed)))
    def test_handoff_deterministic_preserves_detail_and_identity(self):
        lock=freeze(self.scene,self.view);a=compile_handoff(lock);b=compile_handoff(copy.deepcopy(lock))
        self.assertEqual(a,b);self.assertEqual(a['physical_invariants']['delivery_counts'],{'slab':1})
        self.assertEqual(a['visual_plan']['plans']['light_material_plan']['material_default_by_kind'],{'slab':'concrete'})
    def test_request_budget_never_silently_truncates(self):
        lock=freeze(self.scene,self.view)
        with self.assertRaisesRegex(ValueError,'character budget'):request(lock,'slab','x'*31000)
        self.assertLess(len(request(lock,'slab','Neutral graphite')),30000)


if __name__=='__main__':unittest.main()
