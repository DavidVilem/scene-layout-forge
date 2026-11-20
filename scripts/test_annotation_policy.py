import copy,unittest
from annotation_policy import configure,errors,instruction
from pixel_review import requirements
from scene_schema import shape_errors
from scene_model import KINDS

class AnnotationPolicyTests(unittest.TestCase):
    def setUp(self):self.scene={'parts':[],'callouts':[{'id':'x','target':'a','text':'PANEL'}],'labels':[{'text':'old'}]}
    def test_short_request_defaults_to_no_labels_without_mutation(self):
        original=copy.deepcopy(self.scene);s=configure(self.scene)
        self.assertEqual(s['callouts'],[]);self.assertEqual(s['labels'],[])
        self.assertEqual(s['delivery_counts']['annotations'],0);self.assertEqual(self.scene,original)
        self.assertFalse(errors(s,required=True));self.assertIn('ANNOTATIONS OFF',instruction(s))
    def test_requested_labels_keep_exact_map(self):
        s=configure(self.scene,requested=True,request_excerpt='Include one English annotation')
        self.assertEqual(s['callouts'],self.scene['callouts']);self.assertFalse(errors(s))
    def test_request_evidence_required(self):
        with self.assertRaises(ValueError):configure(self.scene,requested=True)
    def test_disabled_labels_fail_core_shape_validation(self):
        s=configure(self.scene);s['callouts']=self.scene['callouts']
        self.assertTrue(shape_errors(s,KINDS))
    def test_count_mismatch_rejected(self):
        s=configure(self.scene);s['delivery_counts']['annotations']=5;self.assertTrue(errors(s))
    def test_legacy_fixture_readable_but_not_current_delivery(self):
        self.assertEqual(errors(self.scene),[]);self.assertTrue(errors(self.scene,required=True))
    def test_absence_requires_pixel_observation(self):
        s=configure(self.scene);self.assertIn('global:annotations',requirements({'scene':s}))
    def test_disabling_labels_preserves_design_detail_and_view(self):
        self.scene.update(camera={'azimuth':35},detail_regions=[{'name':'urban'}],connections=[{'id':'route'}])
        s=configure(self.scene)
        for k in ('camera','detail_regions','connections'):self.assertEqual(s[k],self.scene[k])

if __name__=='__main__':unittest.main()
