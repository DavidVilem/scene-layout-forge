import copy
import unittest
import numpy as np

from drawing_style import surface_coordinates,surface_hatching
from surface_mapping import TriangleMap
from scene_model import make_part,validate
from render_scene import build,Renderer
from registered_geometry import signature,contact_errors
from visual_contract import MaterialSpec,compile_visual_contract


def folded_fixture():
    vertices=[[0,0,0],[1,0,0],[2,0,.6],[0,1,0],[1,1,0],[2,1,.6]]
    part=make_part('folded-panel','custom',[0,0,0],[2,1,.6],parameters={
        'adapter':'registered-folded-panel','limitations':'Prescribed surface shape only; no bending mechanics.',
        'vertices':vertices,'faces':[[0,1,4],[0,4,3],[1,2,5],[1,5,4]],
        'edges':[[0,1],[1,2],[2,5],[5,4],[4,3],[3,0],[1,4]]})
    return {'units':'m','schema_version':2,'validation_policy':'strict','registered_geometry':True,
        'parts':[make_part('support','slab',[-.1,-.1,-.2],[1.2,1.2,.2]),part],
        'grounded':['support'],'bearings':[{'part':'folded-panel','on':'support'}],
        'custom_contacts':[{'part':'folded-panel','on':'support','points':[[.1,.1,0],[.8,.1,0],[.8,.8,0],[.1,.8,0]]}],
        'light_material_plan':{'ambient':.8,'key_strength':.2,'materials':{'folded-panel':{
            'family':'wood','mapping':'registered','vertex_uv':[[0,0],[1,0],[2,0],[0,1],[1,1],[2,1]],
            'spacing':.17,'density':.35,'base_value':170}}}}


class SurfaceTransportTests(unittest.TestCase):
    def test_grain_wraps_corner_with_shared_edge_and_keeps_progressing(self):
        first=TriangleMap([[0,0,0],[1,0,0],[1,1,0]],[[0,0],[1,0],[1,1]])
        second=TriangleMap([[1,0,0],[1,0,1],[1,1,0]],[[1,0],[2,0],[1,1]])
        seam=np.array([[1,t,0] for t in np.linspace(.05,.9,20)])
        spec={'family':'wood','mapping':'registered','spacing':.19}
        np.testing.assert_allclose(surface_coordinates(seam,spec,first),surface_coordinates(seam,spec,second))
        np.testing.assert_allclose(surface_hatching(seam,spec,[0,0,1],[170]*3,first),
                                   surface_hatching(seam,spec,[-1,0,0],[170]*3,second))
        # The second face's world X is constant: a world-plane projection would
        # freeze the pattern here, whereas transported material U keeps growing.
        u,_=second.coordinates([[1,.1,.05],[1,.1,.4],[1,.1,.8]])
        np.testing.assert_allclose(u,[1.05,1.4,1.8])

    def test_material_samples_follow_registered_deformation_and_rigid_motion(self):
        uv=[[0,0],[1,0],[0,1]]
        flat=np.array([[0,0,0],[1,0,0],[0,1,0]],float)
        bent=np.array([[0,0,0],[1.4,.2,.6],[-.1,.8,.3]],float)
        weights=np.array([[.6,.2,.2],[.1,.6,.3],[.2,.1,.7],[.45,.5,.05]])
        spec={'family':'cloth','mapping':'registered','spacing':.13,'density':.3}
        a=surface_hatching(weights@flat,spec,[0,0,1],[180]*3,TriangleMap(flat,uv))
        b=surface_hatching(weights@bent,spec,[-.4,-.2,1],[180]*3,TriangleMap(bent,uv))
        np.testing.assert_allclose(a,b,atol=1e-10)
        rotation=np.array([[0,-1,0],[1,0,0],[0,0,1]])
        moved=bent@rotation.T+[4,-2,3]
        np.testing.assert_allclose(TriangleMap(moved,uv).coordinates(weights@moved),
                                   TriangleMap(flat,uv).coordinates(weights@flat),atol=1e-12)

    def test_cylinder_marks_agree_at_facets_and_periodic_seam(self):
        spec={'family':'matte_metal','mapping':'cylindrical','spacing':.17,'density':.3}
        for angle in [2*np.pi*k/24 for k in range(24)]+[np.pi]:
            points=np.array([[np.cos(angle+delta),np.sin(angle+delta),.37] for delta in (-1e-9,1e-9)])
            marks=surface_hatching(points,spec,[np.cos(angle),np.sin(angle),0],[170]*3)
            self.assertAlmostEqual(float(marks[0]),float(marks[1]),places=5)

    def test_registered_rebuild_transports_pattern_and_keeps_actual_support_patch(self):
        original=folded_fixture();deformed=copy.deepcopy(original)
        panel=deformed['parts'][1];panel['size']=[2.4,1,.9]
        for index in (2,5):panel['parameters']['vertices'][index]=[2.4,index==5,.9]
        self.assertEqual(validate(deformed),[])
        self.assertEqual(deformed['custom_contacts'],original['custom_contacts'])
        weights=np.array([[.6,.2,.2],[.2,.5,.3],[.1,.2,.7]])
        samples=[];signatures=[]
        for scene in (original,deformed):
            mesh=build(scene);renderer=Renderer(mesh,220,200);renderer.draw(mesh)
            signatures.append(signature(mesh))
            # This map came from build()/Renderer, not a duplicate test surface.
            index=next(i for i,ids in mesh.surface_face_indices.items() if ids==(1,2,5))
            world=weights@np.asarray(mesh.faces[index][0]);spec=renderer.light_material_plan['materials']['folded-panel']
            samples.append(surface_hatching(world,spec,[0,0,1],[170]*3,renderer.surface_maps[index]))
        self.assertNotEqual(*signatures)
        np.testing.assert_allclose(*samples,atol=1e-10)

    def test_material_ablation_retains_registered_geometry_contacts_depth_and_owner(self):
        scene=folded_fixture();self.assertEqual(validate(scene),[])
        before=copy.deepcopy(scene);mesh=build(scene);mesh_signature=signature(mesh)
        a=Renderer(mesh,320,280,finish='graphite');ia=np.asarray(a.draw(mesh))
        ablated=copy.deepcopy(scene['light_material_plan'])
        ablated['materials']['folded-panel']['mark']='none'
        b=Renderer(mesh,320,280,finish='graphite',light_material_plan=ablated);ib=np.asarray(b.draw(mesh))
        np.testing.assert_array_equal(a.z,b.z);np.testing.assert_array_equal(a.owner,b.owner)
        self.assertEqual(signature(mesh),mesh_signature);self.assertEqual(scene,before)
        self.assertEqual(contact_errors(scene),[])
        self.assertGreater(np.count_nonzero(ia!=ib),100)
        changed=copy.deepcopy(scene);changed['light_material_plan']=ablated
        self.assertEqual(signature(build(changed)),mesh_signature)

    def test_perspective_clipping_retains_same_surface_map_and_ownership(self):
        scene=folded_fixture();mesh=build(scene)
        options=dict(width=320,height=280,projection='perspective',camera_eye=[.5,-.3,.5],
                     camera_target=[1,.5,.2],near=.6,fov=90)
        a=Renderer(mesh,**options);a.draw(mesh)
        b=Renderer(mesh,hatching=False,**options);b.draw(mesh)
        self.assertGreater(np.count_nonzero(a.owner==a.part_ids['folded-panel']),100)
        np.testing.assert_array_equal(a.z,b.z);np.testing.assert_array_equal(a.owner,b.owner)

    def test_invalid_uv_geometry_is_rejected_without_planar_fallback(self):
        original=folded_fixture()
        changes=[lambda s:s['light_material_plan']['materials']['folded-panel'].update(vertex_uv=[[0,0]]*6),
                 lambda s:s['light_material_plan']['materials']['folded-panel']['vertex_uv'].pop(),
                 lambda s:s['parts'][1]['parameters'].update(faces=[[0,1,4,3]]),
                 lambda s:s['parts'][1].update(kind='wall')]
        for change in changes:
            scene=copy.deepcopy(original);change(scene)
            self.assertEqual(compile_visual_contract(scene)['status'],'failed')
            with self.assertRaises(ValueError):build(scene)
        with self.assertRaises(ValueError):MaterialSpec(family='wood',mapping='registered',vertex_uv=[[0,0],[1,0],[0,float('nan')]])
        with self.assertRaises(ValueError):surface_coordinates([[0,0,0]],{'mapping':'registered'})
        with self.assertRaises(ValueError):TriangleMap([[0,0,0]]*3,[[0,0],[1,0],[0,1]])

    def test_style_seed_is_reproducible_and_cannot_move_geometry(self):
        scene=folded_fixture();mesh=build(scene);geometry=signature(mesh)
        for finish in ('graphite','technical'):
            a=Renderer(mesh,240,220,finish=finish);ia=np.asarray(a.draw(mesh))
            b=Renderer(mesh,240,220,finish=finish,style_seed=0);ib=np.asarray(b.draw(mesh))
            c=Renderer(mesh,240,220,finish=finish,style_seed=19);ic=np.asarray(c.draw(mesh))
            np.testing.assert_array_equal(ia,ib)
            self.assertGreater(np.count_nonzero(ia!=ic),1000)
            np.testing.assert_array_equal(a.z,c.z);np.testing.assert_array_equal(a.owner,c.owner)
            self.assertEqual(signature(mesh),geometry)
        for bad in (-1,True,1.5):
            with self.assertRaisesRegex(ValueError,'style_seed'):Renderer(mesh,style_seed=bad)


if __name__=='__main__':unittest.main()
