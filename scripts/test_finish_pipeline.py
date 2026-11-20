import copy
import unittest
from finish_contract import preflight, freeze, request, check
from view_contract import digest


class FinishPipelineTests(unittest.TestCase):
    def scene(self):
        return {'units':'m','parts':[{'id':'plate','kind':'slab','origin':[0,0,0],'size':[2,2,.2]}],
                'connections':[], 'expected_counts':{'slab':1},
                'detail_regions':[{'name':'foundation','primary':['plate'],'secondary':[],
                                   'quiet_reason':'Simple exposed slab','microdetails':'edge joints'}],
                'callouts':[]}

    def test_legacy_lock_preserves_partial_scope(self):
        lock=freeze(self.scene())
        self.assertEqual(lock['validation']['status'],'partial')

    def test_architecture_handoff_has_no_unrelated_process_instruction(self):
        prompt=request(freeze(self.scene()),'Draw an architectural foundation','Neutral graphite')
        self.assertNotIn('sump',prompt)
        self.assertNotIn('pump',prompt)

    def test_strict_preflight_requires_realized_design(self):
        scene=self.scene();scene['validation_policy']='strict';scene['grounded']=['plate']
        self.assertIn('strict finish requires design intent, selection and realization evidence',preflight(scene))

    def test_modified_view_invalidates_frozen_handoff(self):
        scene=self.scene()
        view={'scene_sha256':digest(scene),'camera':{},'annotations':[],
              'guide_sha256':'fixture','image_size':[20,20]}
        lock=freeze(scene,view)
        view['guide_sha256']='changed-original-object'
        check(lock,scene)  # snapshot does not alias caller data
        lock['view']['guide_sha256']='different-guide'
        with self.assertRaisesRegex(ValueError,'view evidence'):
            check(lock,scene)


if __name__=='__main__':unittest.main()
