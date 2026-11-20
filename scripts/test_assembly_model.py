"""Assembly placement and real apertures: invariance, conservation and failures."""
import copy
import itertools
import math
import unittest

from assembly_model import (RigidTransform, bed, workbench, elevator_shaft,
                            compose_assembly, cut_host, opening_errors, compile_cutaway,
                            stair_obstructs_volume)
from scene_model import validate


def box(name, kind='wall', origin=(0,0,0), size=(6,.3,3), **extra):
    return dict(id=name, kind=kind, origin=list(origin), size=list(size), **extra)


def volume(parts):
    return sum(math.prod(p['size']) for p in parts)


class AssemblyTests(unittest.TestCase):
    def assertVectorAlmostEqual(self,a,b):
        for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=7)

    def test_transform_inverse_and_composition(self):
        parent=RigidTransform((7,-2,3),37);child=RigidTransform((1,5,2),-13);point=[2,3,4]
        self.assertVectorAlmostEqual(parent.inverse().point(parent.point(point)),point)
        self.assertVectorAlmostEqual(parent.compose(child).point(point),parent.point(child.point(point)))

    def test_transform_rejects_nonfinite(self):
        with self.assertRaises(ValueError):RigidTransform((0,float('nan'),0))
        with self.assertRaises(ValueError):RigidTransform(yaw=True)

    def test_port_and_route_coincidence_after_translation_and_quarter_turn(self):
        scene={'units':'m','parts':[box('a',size=(1,1,1),ports={'out':[1,.5,.5]}),
                                     box('b',origin=(3,0,0),size=(1,1,1),ports={'in':[0,.5,.5]})],
               'connections':[{'from':'a:out','to':'b:in','route':[[1,.5,.5],[3,.5,.5]],'radius':.05}]}
        for yaw in (0,90,-90,180):
            placed=compose_assembly(scene,RigidTransform((4,-3,2),yaw),'module/')
            self.assertEqual(validate(placed),[])
            self.assertEqual(placed['connections'][0]['from'],'module/a:out')
            self.assertEqual(scene['parts'][0]['origin'],[0,0,0])

    def test_attachment_coincidence_after_arbitrary_rotation(self):
        scene={'units':'m','parts':[box('a',size=(1,1,1),ports={'face':[1,.5,.5]}),
                                     box('b',origin=(1,0,0),size=(1,1,1),ports={'face':[0,.5,.5]})],
               'attachments':[{'from':'a:face','to':'b:face'}]}
        placed=compose_assembly(scene,RigidTransform((2,4,1),27),'rot/')
        self.assertEqual(validate(placed),[])
        self.assertEqual(len(placed['placement']['baked_parts']),2)
        self.assertTrue(placed['placement']['unverified'])

    def test_directional_stair_keeps_real_shape_under_rotation(self):
        from render_scene import build
        stair=box('stair','stair',(0,0,0),(1.2,3,2),parameters={'steps':10})
        scene={'units':'m','parts':[stair]};transform=RigidTransform((6,3,0),41)
        source=build(scene)
        placed=compose_assembly(scene,transform)
        part=placed['parts'][0]
        self.assertEqual(part['source_kind'],'stair')
        self.assertEqual(part['kind'],'custom')
        expected=[transform.point(v.tolist()) for face,_ in source.faces for v in face]
        actual=[[part['origin'][k]+v[k] for k in range(3)] for v in part['parameters']['vertices'][:len(expected)]]
        for a,b in zip(expected,actual):self.assertVectorAlmostEqual(a,b)
        self.assertEqual(validate(placed),[])

    def test_semantic_assembly_references_are_prefixed(self):
        assembly=workbench('bench');placed=compose_assembly(assembly,RigidTransform((3,2,0),90),'room/')
        ids={p['id'] for p in placed['parts']}
        self.assertTrue(set(placed['assembly']['members'])<=ids)
        self.assertTrue(set(placed['assembly']['ground_contacts'])<=ids)
        self.assertTrue(all(c['part'] in ids and c['on'] in ids for c in placed['bearings']))
        self.assertEqual(validate(placed),[])

    def test_door_aperture_conserves_volume_without_obstruction(self):
        result=cut_host(box('wall'),[dict(id='door',origin=[2,0,0],size=[1,.3,2])],'y')
        self.assertAlmostEqual(volume(result['parts']),6*.3*3-1*.3*2)
        self.assertEqual(opening_errors(result),[])
        for a,b in itertools.combinations(result['parts'],2):
            self.assertFalse(all(min(a['origin'][i]+a['size'][i],b['origin'][i]+b['size'][i])-max(a['origin'][i],b['origin'][i])>1e-8 for i in range(3)))

    def test_overlapping_apertures_subtract_union(self):
        result=cut_host(box('floor','slab',size=(6,6,.25)),[
            dict(id='a',origin=[1,1,-1],size=[2,2,2]),dict(id='b',origin=[2,2,-1],size=[2,2,2])],'z')
        self.assertAlmostEqual(volume(result['parts']),(36-7)*.25)
        self.assertEqual(opening_errors(result),[])

    def test_aperture_ids_and_bounds_transform(self):
        result=cut_host(box('wall'),[dict(id='door',origin=[2,0,0],size=[1,.3,2])],'y')
        placed=compose_assembly(result,RigidTransform((10,2,0),90),'room/')
        self.assertEqual(opening_errors(placed),[])
        self.assertEqual(placed['openings'][0]['normal_axis'],'x')
        self.assertEqual(placed['hosts'][0]['id'],'room/wall')
        with self.assertRaisesRegex(ValueError,'oriented opening'):
            compose_assembly(result,RigidTransform(yaw=33))

    def test_invalid_apertures_fail(self):
        for opening in [dict(id='short',origin=[2,.1,0],size=[1,.1,2]),
                        dict(id='outside',origin=[7,0,0],size=[1,.3,2]),
                        dict(id='all',origin=[0,0,0],size=[6,.3,3])]:
            with self.assertRaises(ValueError):cut_host(box('wall'),[opening],'y')
        with self.assertRaises(ValueError):cut_host(box('vessel','vessel'),[],'y')
        with self.assertRaises(ValueError):cut_host(box('wall',parameters={'profile':'I'}),[],'y')

    def test_obstruction_and_misfit_fill_detected(self):
        result=cut_host(box('wall'),[dict(id='door',origin=[2,0,0],size=[1,.3,2],filled_by='door-leaf')],'y')
        result['parts'].append(box('door-leaf','door',origin=(2,0,0),size=(1,.3,2)))
        self.assertEqual(opening_errors(result),[])
        result['parts'][-1]['size'][0]=2
        self.assertTrue(any('fit' in e for e in opening_errors(result)))
        result['parts'][0]['origin']=[2,0,0];result['parts'][0]['size']=[.2,.3,.2]
        self.assertTrue(any('obstructs' in e for e in opening_errors(result)))

    def test_cutaway_does_not_mutate_complete_physical_scene(self):
        physical={'units':'m','parts':[box('roof','slab',size=(6,6,.3)),box('wall',origin=(0,0,-3))]}
        original=copy.deepcopy(physical)
        display=compile_cutaway(physical,['roof'],[dict(host='wall',axis='z',value=-1,keep='lower')])
        self.assertEqual(physical,original)
        self.assertEqual([p['id'] for p in display['parts']],['wall'])
        self.assertAlmostEqual(display['parts'][0]['size'][2],2)
        self.assertEqual(len(display['representation']['physical_sha256']),64)
        self.assertEqual(validate(display),[])

    def test_cutaway_removes_only_display_connections_to_hidden_parts(self):
        physical={'units':'m','parts':[box('a',size=(1,1,1),ports={'out':[1,.5,.5]}),
                                     box('b',origin=(3,0,0),size=(1,1,1),ports={'in':[0,.5,.5]},parent='a')],
               'connections':[{'from':'a:out','to':'b:in','route':[[1,.5,.5],[3,.5,.5]],'radius':.05}]}
        display=compile_cutaway(physical,['a'])
        self.assertEqual(display['connections'],[])
        self.assertEqual(len(physical['connections']),1)
        self.assertEqual(validate(display),[])

    def test_cutaway_rejects_undefined_or_unsupported_cuts(self):
        physical={'units':'m','parts':[box('vessel','vessel')]}
        with self.assertRaises(ValueError):compile_cutaway(physical,['missing'])
        with self.assertRaises(ValueError):compile_cutaway(physical,cuts=[dict(host='vessel',axis='z',value=1,keep='lower')])

    def test_semantic_parts_are_not_cabinet_proxies(self):
        for assembly in (bed(),workbench(),elevator_shaft()):
            self.assertFalse(any(p['kind']=='cabinet' for p in assembly['parts']))
            self.assertEqual(validate(assembly),[])
        lift=elevator_shaft(height=12,cabin_z=4)
        self.assertEqual(sum(p['id'].endswith('/cabin-floor') for p in lift['parts']),1)
        self.assertEqual(lift['assembly']['required_clear_volume']['size'][2],12)
        self.assertIn('suspension',lift['assembly']['limitations'])

    def test_stair_narrowphase_distinguishes_headroom_from_box_overlap(self):
        stair=box('upper','stair',(0,-3,3.5),(1.6,6,3.5),parameters={'steps':20})
        # Lower flight's near-top walking body is beneath upper flight treads.
        clear={'min':[.5,2.4,4.5],'max':[1.1,2.9,5.5]}
        self.assertFalse(stair_obstructs_volume(stair,clear))
        # Reversing the upper flight puts its low treads in that body envelope.
        stair['parameters']['reverse']=True
        conflict={'min':[.5,.0,4.0],'max':[1.1,.4,5.4]}
        self.assertTrue(stair_obstructs_volume(stair,conflict))
        self.assertTrue(stair_obstructs_volume(stair,{'min':[0,0,0]}))


if __name__=='__main__':unittest.main()
