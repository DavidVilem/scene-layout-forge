import copy,json,unittest
from assembly_model import RigidTransform
from room_programs import PROGRAMS,program_assembly,place_program
from scene_model import make_part,validate
from build_bunker import build_scene

def fixture(program,seed=52,variant=0):
    scene={'units':'m','schema_version':2,'validation_policy':'strict','registered_geometry':True,
        'parts':[make_part('floor','slab',[-4,-4,-.2],[8,8,.2]),make_part('north','wall',[-4,3.7,0],[8,.2,3.3])],
        'grounded':['floor'],'bearings':[{'part':'north','on':'floor'}],'mounts':[],'assemblies':[]}
    kit=place_program(program,'room',floor_id='floor',wall_parts={'north':['north']},scene_parts=scene['parts'],seed=seed,variant_index=variant)
    for field in ('parts','bearings','mounts','assemblies'):scene[field]+=kit.get(field,[])
    scene['assemblies'].append(kit['assembly'])
    return scene,kit

class RoomProgramTests(unittest.TestCase):
    def test_all_declared_program_variants_have_strict_supports(self):
        for program in PROGRAMS:
            for variant in range(3):
                with self.subTest(program=program,variant=variant):
                    scene,kit=fixture(program,variant=variant)
                    self.assertEqual(validate(scene),[])
                    self.assertGreaterEqual(len(kit['program_recipe']['functional_objects']),5)
    def test_programs_are_functional_assemblies_not_homogeneous_boxes(self):
        expected={'control':{'operator_station','communications_equipment_rack','document_storage'},
            'dormitory':{'bed','personal_locker_bank','personal_luggage_storage'},
            'workshop':{'bench_vise','mounted_tool_storage','underbench_drawer_unit'},
            'medical':{'bed','clinical_supply_cupboard','wall_shelf'},
            'storage':{'storage_rack','palletized_storage','wall_shelf'},
            'utilities':{'mounted_distribution_cupboard','ventilation_fittings','electrical_maintenance_storage'}}
        signatures=[]
        for program,roles in expected.items():
            kit=program_assembly(program)
            found={a['role'] for a in kit['assemblies']}
            self.assertTrue(roles<=found,(program,found));signatures.append(tuple(sorted(found)))
            self.assertTrue(all(p.get('semantic_role') and p.get('design_program')==program for p in kit['parts']))
        self.assertEqual(len(set(signatures)),6)
        self.assertEqual(len({v['fine_detail'] for v in PROGRAMS.values()}),6)
    def test_same_seed_reproduces_and_neighboring_rooms_vary_secondaries(self):
        for program in PROGRAMS:
            kits=[program_assembly(program,seed=52,variant_index=i) for i in range(3)]
            self.assertEqual(kits[0],program_assembly(program,seed=52))
            self.assertEqual({k['program_recipe']['variant'] for k in kits},{0,1,2})
            self.assertEqual(len({json.dumps(k['parts'],sort_keys=True) for k in kits}),3)
            seeded={json.dumps(program_assembly(program,seed=s)['parts'],sort_keys=True) for s in range(8)}
            self.assertGreater(len(seeded),1)
    def test_missing_fixture_contact_is_not_inferred_from_nearby_floor(self):
        scene,_=fixture('control')
        scene['bearings']=[b for b in scene['bearings'] if b['part']!='room/communications-rack']
        self.assertTrue(any('room/communications-rack' in e and 'bearing path' in e for e in validate(scene)))
    def test_missing_wall_fixture_mount_is_rejected(self):
        scene,_=fixture('workshop')
        scene['mounts']=[m for m in scene['mounts'] if m['part']!='room/toolboard']
        self.assertTrue(any('room/toolboard' in e for e in validate(scene)))
    def test_kit_keeps_central_cross_empty_at_walking_height(self):
        for program in PROGRAMS:
            for variant in range(3):
                for p in program_assembly(program,variant_index=variant)['parts']:
                    lo=p['origin'];hi=[lo[i]+p['size'][i] for i in range(3)]
                    if hi[2]<=.01 or lo[2]>=2.15:continue
                    self.assertFalse(lo[0]<.9-1e-8 and hi[0]>-.9+1e-8,(program,p['id'],'north-south route'))
                    self.assertFalse(lo[1]<.9-1e-8 and hi[1]>-.9+1e-8,(program,p['id'],'east-west route'))
    def test_external_support_must_exist_and_coincide(self):
        scene,_=fixture('control')
        with self.assertRaisesRegex(ValueError,'floor is absent'):
            place_program('control','x',floor_id='missing',wall_parts={'north':['north']},scene_parts=scene['parts'])
        with self.assertRaisesRegex(ValueError,'actual wall surface'):
            place_program('control','x',floor_id='floor',wall_parts={'north':['north']},scene_parts=scene['parts'],transform=RigidTransform((0,1,0)))
    def test_unknown_program_small_footprint_and_unregistered_rotation_are_explicit(self):
        with self.assertRaisesRegex(ValueError,'unsupported'):program_assembly('operating_theatre')
        with self.assertRaisesRegex(ValueError,'footprint'):program_assembly('control',width=6)
        with self.assertRaisesRegex(ValueError,'translation-only'):
            place_program('control','x',floor_id='floor',wall_parts={},scene_parts=[],transform=RigidTransform(yaw=90))

class BunkerRoomIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scene=build_scene(52,family='branched')
    def test_enrichment_preserves_strict_access_and_five_stair_flights(self):
        self.assertEqual(validate(self.scene),[])
        self.assertEqual(sum(p['kind']=='stair' for p in self.scene['parts']),5)
        self.assertEqual(len(self.scene['room_programs']),24)
        for level in range(6):
            recipes=[self.scene['room_programs'][f'L{level}Z{i}'] for i in range(1,5)]
            self.assertEqual({r['variant'] for r in recipes},{0,1,2})
    def test_each_delivery_region_has_three_meaningful_secondary_targets(self):
        ids={p['id'] for p in self.scene['parts']}
        for r in self.scene['detail_regions']:
            self.assertGreaterEqual(len(set(r['secondary'])),3)
            self.assertTrue(set(r['secondary'])<=ids)
        self.assertEqual(len({r['microdetails'] for r in self.scene['detail_regions']}),len(self.scene['detail_regions']))
    def test_new_fixture_blocking_corridor_is_rejected(self):
        scene=copy.deepcopy(self.scene);anchor=scene['materialized_design']['zones']['L0Z1']['anchor']
        p=next(p for p in scene['parts'] if p['id']=='L0Z1/communications-rack')
        delta=[anchor[0]-.6-p['origin'][0],anchor[1]-.3-p['origin'][1],0]
        for q in scene['parts']:
            if q['id']==p['id'] or q['id'].startswith(p['id']+'/'):
                q['origin']=[v+delta[i] for i,v in enumerate(q['origin'])]
        self.assertTrue(any('occupied walking envelope' in e for e in validate(scene)))

if __name__=='__main__':unittest.main()
