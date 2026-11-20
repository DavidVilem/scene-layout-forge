import copy
import math
import unittest

from scene_model import make_part,validate,validation_report
from coherence_validation import coherence_report
from physical_support import support_checks,contact_patch_status
from relation_contracts import relation_report,witness_errors
from access_geometry import volume_obstructed
from functional_contracts import functional_checks
from route_contracts import route_checks


def base():
    return dict(units='m',schema_version=2,validation_policy='strict',grounded=['floor'],
        parts=[make_part('floor','slab',[-2,-2,-.2],[12,12,.2]),make_part('box','cabinet',[0,0,0],[1,1,1])],
        bearings=[dict(part='box',on='floor')])


def ramp_scene():
    s=base();s['parts']=s['parts'][:1]+[make_part('ramp','ramp',[0,0,0],[1,3,1]),
        make_part('landing','slab',[0,3,.8],[1,1,.2]),make_part('post','column',[0,3,0],[1,1,.8])]
    s['bearings']=[dict(part='ramp',on='floor'),dict(part='post',on='floor'),dict(part='landing',on='post')]
    s['ramp_access']=[dict(ramp='ramp',landing='landing')]
    s['access_nodes']=[dict(id='a',position=[.5,.3,1.3]),dict(id='b',position=[.5,3.5,2.2])];s['access_roots']=['a']
    s['access_volumes']=[dict(id='walk',min=[.4,.2,.4],max=[.6,3.6,3.2],from_='a',to='b',
        traversable_parts=['ramp'],walking_path=[[.5,.3,1.3],[.5,3.5,2.2]],body_below=.9,body_above=1.,half_width=.1)]
    s['access_volumes'][0]['from']=s['access_volumes'][0].pop('from_')
    return s


class FunctionalCoverageTests(unittest.TestCase):
    def test_nonpump_contract_is_reported_as_unsupported(self):
        s=base();s['functional_contracts']=[dict(id='c',part='box',role='electrical_control')]
        rows=[c for c in coherence_report(s)['checks'] if c['check']=='functional']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['contract_id'],'c');self.assertEqual(rows[0]['status'],'unsupported')
        self.assertTrue(validate(s))

    def test_each_declared_contract_has_exactly_one_result(self):
        s=base();s['functional_contracts']=[dict(id='a',part='box',role='unknown'),dict(id='b',part='missing',role='stored')]
        rows=functional_checks(s)
        self.assertEqual([c['contract_id'] for c in rows],['a','b']);self.assertEqual([c['status'] for c in rows],['unsupported','failed'])

    def test_same_part_distinct_contracts_do_not_disappear(self):
        s=base();s['functional_contracts']=[dict(id='a',part='box',role='unknown'),dict(id='b',part='box',role='unknown2')]
        self.assertEqual(len(functional_checks(s)),2)

    def test_program_name_cannot_replace_required_components(self):
        s=base();s['functional_contracts']=[dict(part='box',role='component_set',members=['box'],required_kinds=['pump'])]
        self.assertEqual(functional_checks(s)[0]['status'],'failed')


class AccessSolidTests(unittest.TestCase):
    def test_supported_ramp_has_supported_adapter(self):
        self.assertEqual(validate(ramp_scene()),[])

    def test_floating_ramp_fails(self):
        s=ramp_scene();s['bearings']=s['bearings'][1:]
        self.assertTrue(any('bearing path' in e for e in validate(s)))

    def test_traversable_ramp_is_not_solid_exemption(self):
        s=ramp_scene();v=s['access_volumes'][0];v.pop('walking_path');v['min'][2]=.1
        self.assertTrue(any('occupied walking' in e for e in validate(s)))

    def test_traversable_stair_is_not_solid_exemption(self):
        stair=make_part('flight','stair',[0,0,0],[1,3,2],parameters={'steps':10})
        v=dict(min=[.1,.1,.1],max=[.9,2.9,3],traversable_parts=['flight'])
        self.assertTrue(volume_obstructed(stair,v))

    def test_wall_still_blocks_ramp_profile(self):
        s=ramp_scene();s['parts'].append(make_part('wall','wall',[0,2,0],[1,.15,3]));s['bearings'].append(dict(part='wall',on='floor'))
        self.assertTrue(any('occupied walking' in e for e in validate(s)))

    def test_forged_sweep_cannot_leave_envelope_or_nodes(self):
        s=ramp_scene();s['access_volumes'][0]['walking_path'][0][2]+=4
        self.assertTrue(any('walking_path endpoints' in e for e in validate(s)))


class SupportWitnessTests(unittest.TestCase):
    def plane_scene(self):
        return dict(units='m',schema_version=2,validation_policy='strict',support_contract_version=1,
            grounded=['root'],parts=[make_part('root','footing',[0,0,0],[1,1,.2])],
            ground_surfaces=[dict(id='earth',type='plane',point=[0,0,0],normal=[0,0,1],bounds=dict(min=[-1,-1,0],max=[2,2,0]))],
            ground_contacts=[dict(part='root',surface='earth',points=[[.1,.1,0],[.9,.1,0],[.9,.9,0],[.1,.9,0]])])

    def test_explicit_ground_patch_passes(self):self.assertEqual(validate(self.plane_scene()),[])

    def test_root_above_ground_fails_even_if_grounded(self):
        s=self.plane_scene();s['parts'][0]['origin'][2]=.02
        self.assertTrue(any('ground contact misses' in e for e in validate(s)))

    def test_plane_hole_missing_surface_bounds_fails(self):
        s=self.plane_scene();s['ground_surfaces'][0]['bounds']['max'][0]=.2
        self.assertTrue(any('outside registered' in e for e in validate(s)))

    def test_ground_root_needs_explicit_patch_in_v1(self):
        s=self.plane_scene();s['ground_contacts']=[]
        self.assertTrue(any('Explicit ground contact' in e for e in validate(s)))

    def test_sloped_translated_ground_uses_world_contact_frame(self):
        s=self.plane_scene();normal=[-.2/math.sqrt(1.04),0,1/math.sqrt(1.04)]
        verts=[[0,0,0],[2,0,.4],[2,2,.4],[0,2,0],[0,0,1],[2,0,1.4],[2,2,1.4],[0,2,1]]
        s['parts']=[make_part('root','custom',[3,4,2],[2,2,1.4],parameters=dict(adapter='sloped-root',limitations='geometry only',vertices=verts,faces=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]))]
        s['registered_geometry']=True;s['ground_surfaces']=[dict(id='earth',type='plane',point=[3,4,2],normal=normal,bounds=dict(min=[3,4,2],max=[5,6,2.4]))]
        s['ground_contacts'][0]['points']=[[3.2,4.2,2.04],[4.8,4.2,2.36],[4.8,5.8,2.36],[3.2,5.8,2.04]]
        self.assertEqual(validate(s),[])
        s['ground_contacts'][0]['points'][0][2]+=.01
        self.assertTrue(any('detached from plane' in e for e in validate(s)))

    def test_corner_only_contact_is_unsupported(self):
        s=base();status,_=contact_patch_status(s,dict(part='box',on='floor',points=[[0,0,0],[.5,0,0],[1,0,0]]))
        self.assertEqual(status,'unsupported')

    def test_root_reaching_cycle_needs_justification(self):
        s=base();s['mounts']=[dict(part='floor',on='box',axis='z',side=-1)]
        self.assertTrue(any(c['status']=='failed' and 'cycle' in c['message'] for c in support_checks(s)))


class RelationTests(unittest.TestCase):
    def test_localized_contact_witness(self):
        s=base();w=dict(relation_id='bearing:box->floor',point=[.5,.5,0],owners=['box','floor'])
        self.assertEqual(witness_errors(s,w),[])
        w['point']=[5,5,0]
        self.assertTrue(any('outside' in e for e in witness_errors(s,w)))

    def test_proximity_without_relation_is_not_contact(self):
        s=base();s['bearings']=[]
        self.assertTrue(witness_errors(s,dict(relation_id='bearing:box->floor',point=[.5,.5,0],owners=['box','floor'])))

    def test_unknown_critical_relation_blocks_strict(self):
        s=base();s['relations']=[dict(id='mystery',type='magnetic_suspension')]
        self.assertEqual(relation_report(s)['checks'][-1]['status'],'unsupported');self.assertTrue(validate(s))

    def test_rigid_mount_verifies_local_frames_and_surface_normals(self):
        s=base();s['relations']=[dict(id='mount',type='rigid_mount',a=dict(part='box',anchor=[.5,.5,0],normal=[0,0,-1]),
            b=dict(part='floor',anchor=[2.5,2.5,.2],normal=[0,0,1]),points=[[.1,.1,0],[.9,.1,0],[.9,.9,0],[.1,.9,0]])]
        self.assertEqual(validate(s),[])
        s['relations'][0]['b']['anchor'][2]+=.01
        self.assertTrue(any('detached' in e for e in validate(s)))

    def test_large_tolerance_cannot_hide_gap(self):
        s=base();s['relations']=[dict(id='x',type='rigid_mount',tolerance=.1)]
        self.assertTrue(any('tolerance' in e for e in validate(s)))


class RouteEvidenceTests(unittest.TestCase):
    def fixture(self):
        from typed_interfaces import add_interface
        s=base();s['parts']=s['parts'][:1]
        a=make_part('a','manifold',[0,0,0],[1,.4,.4]);b=make_part('b','manifold',[4,0,0],[1,.4,.4])
        add_interface(a,'out',[1,.2,.2],[1,0,0],.1,'outlet');add_interface(b,'in',[0,.2,.2],[-1,0,0],.1,'inlet')
        s['parts'] += [a,b];s['bearings']=[dict(part=k,on='floor') for k in ('a','b')]
        s['connections']=[dict(contract_id='supply',from_='a:out',to='b:in',radius=.05,route=[[1.12,.2,.2],[2,.2,.2],[3.88,.2,.2]])]
        s['connections'][0]['from']=s['connections'][0].pop('from_')
        s['route_contracts']=[dict(id='supply',from_='a:out',to='b:in',medium='water',min_bend_radius=.2)]
        s['route_contracts'][0]['from']=s['route_contracts'][0].pop('from_');s['route_contract_version']=1
        return s

    def test_logical_and_spatial_route_agree(self):self.assertEqual(validate(self.fixture()),[])

    def test_changed_destination_fails_network_contract(self):
        s=self.fixture();s['route_contracts'][0]['to']='unrelated:in'
        self.assertEqual(route_checks(s)[0]['status'],'failed')

    def test_too_tight_elbow_fails_declared_radius(self):
        s=self.fixture();s['connections'][0]['route']=[[1.12,.2,.2],[1.22,.2,.2],[1.22,.3,.2],[3.88,.2,.2]]
        self.assertTrue(any('elbow radius' in c['message'] for c in route_checks(s)))

    def test_missing_route_support_cannot_pass_count_based_claim(self):
        s=self.fixture();s['route_contracts'][0]['max_unsupported_length']=.5
        self.assertTrue(any('unsupported length' in c['message'] for c in route_checks(s)))

    def test_pipe_passes_actual_wall_opening_but_not_solid_wall(self):
        from assembly_model import cut_host
        s=self.fixture();host=make_part('wall','wall',[2.5,-.5,0],[.2,1.4,2])
        cut=cut_host(host,[dict(id='sleeve',origin=[2.5,0,0],size=[.2,.4,.4])],'x')
        s['parts']+=cut['parts'];s.update(hosts=cut['hosts'],openings=cut['openings'])
        # Clearance is checked against actual split solids; support of the small
        # lintel is a separate gate, so this test isolates route clearance.
        from scene_model import validate
        self.assertFalse(any('Route clearance' in e for e in validate(s)))
        s['parts']=[p for p in s['parts'] if not p['id'].startswith('wall/')]+[host]
        self.assertTrue(any('Route clearance' in e for e in validate(s)))


if __name__=='__main__':unittest.main()
