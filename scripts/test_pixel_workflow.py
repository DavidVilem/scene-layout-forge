import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from finish_contract import freeze,correction,request
from pixel_review import requirements,create_review,errors,image_identity
from run_manifest import manifest,compare
from run_lifecycle import new_output,new_temporary,owned_record,cleanup_plan


def scene():
    return {'units':'m','parts':[{'id':'plate','kind':'slab','origin':[0,0,0],'size':[2,2,.2]}],
            'connections':[],'expected_counts':{'slab':1},'delivery_counts':{'slab':1},
            'detail_regions':[{'name':'foundation','primary':['plate'],'secondary':[],
                               'quiet_reason':'Simple exposed slab','microdetails':'edge joints'}],'callouts':[]}


class PixelWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.root=Path(self.directory.name)
        self.image=self.root/'final.png';Image.new('RGB',(20,14),'white').save(self.image)
        self.lock=freeze(scene());self.observations=[{'target':key,'state':'visible_correct','note':'Inspected in test fixture'} for key in requirements(self.lock)]
    def tearDown(self):self.directory.cleanup()
    def review(self):return create_review(self.lock,self.image,self.observations,'test supplied observations')
    def test_identity_and_coverage_pass(self):self.assertEqual(errors(self.lock,self.image,self.review()),[])
    def test_different_png_invalidates_review(self):
        review=self.review();Image.new('RGB',(20,14),'black').save(self.image)
        self.assertIn('pixel review belongs to another PNG',errors(self.lock,self.image,review))
    def test_missing_observation_is_not_pass(self):
        with self.assertRaisesRegex(ValueError,'missing independent'):create_review(self.lock,self.image,self.observations[:-1],'test')
    def test_uncertainty_stays_limited(self):
        self.observations[0]['state']='uncertain';self.assertEqual(self.review()['status'],'limited')
    def test_visible_error_needs_correction(self):
        self.observations[0]['state']='visible_error';self.assertEqual(self.review()['status'],'needs_correction')
    def test_tampered_status_rejected(self):
        review=self.review();review['status']='limited';self.assertTrue(errors(self.lock,self.image,review))
    def test_nan_region_rejected(self):
        self.observations[0]['region']=[0,0,float('nan'),1]
        with self.assertRaisesRegex(ValueError,'finite normalized'):self.review()
    def test_annotation_tip_cannot_target_non_callout(self):
        self.observations[0]['desired_tip_xy']=[.5,.5]
        with self.assertRaisesRegex(ValueError,'requires a callout'):self.review()
    def test_duplicate_unknown_targets_rejected(self):
        self.observations.append(copy.deepcopy(self.observations[0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):self.review()
    def test_null_observations_cannot_crash_or_pass(self):
        review=self.review();review['observations']=None;self.assertTrue(errors(self.lock,self.image,review))
    def test_invalid_png_rejected(self):
        self.image.write_bytes(b'not a PNG')
        with self.assertRaises(Exception):image_identity(self.image)
    def test_png_extension_does_not_accept_jpeg(self):
        Image.new('RGB',(20,14)).save(self.image,format='JPEG')
        with self.assertRaisesRegex(ValueError,'decode as PNG'):image_identity(self.image)
    def test_localized_correction_needs_bound_pixels(self):
        with self.assertRaisesRegex(ValueError,'inspected PNG'):correction(self.lock,self.lock['scene'],[{'kind':'count','target':'slab','extra_at':[.5,.5]}])
    def test_stale_review_cannot_authorize_correction(self):
        review=self.review();Image.new('RGB',(21,14),'white').save(self.image)
        with self.assertRaisesRegex(ValueError,'another PNG'):correction(self.lock,self.lock['scene'],[{'kind':'tone','target':'paper'}],review=review,image_path=self.image)
    def test_extra_coordinates_bound_to_an_observed_error(self):
        edit=[{'kind':'count','target':'slab','extra_at':[.5,.5]}]
        with self.assertRaisesRegex(ValueError,'localized observed'):correction(self.lock,self.lock['scene'],edit,review=self.review(),image_path=self.image)
        count=next(o for o in self.observations if o['target']=='count:slab');count.update(state='visible_error',region=[.4,.4,.6,.6])
        self.assertIn('invented extra slab',correction(self.lock,self.lock['scene'],edit,review=self.review(),image_path=self.image))
        edit[0]['extra_at']=[.9,.9]
        with self.assertRaisesRegex(ValueError,'outside the observed'):correction(self.lock,self.lock['scene'],edit,review=self.review(),image_path=self.image)
    def test_third_correction_rejected(self):
        with self.assertRaisesRegex(ValueError,'maximum two'):correction(self.lock,self.lock['scene'],[],correction_index=3)
    def test_inventory_separate_from_requested_visible_count(self):
        text=request(self.lock,'Draw slab','Neutral ink')
        self.assertIn('includes parts hidden',text);self.assertIn('Requested delivery counts',text)
    def test_manifest_does_not_infer_image_model(self):
        package=self.root/'package';package.mkdir();(package/'SKILL.md').write_text('revision: "test"',encoding='utf-8')
        result=manifest(package,self.lock,'slab','full handoff',self.image)
        self.assertEqual(result['client']['image_model'],'unreported')
        self.assertNotIn(str(self.root),json.dumps(result));self.assertTrue(compare(result,result)['same_recorded_inputs'])
        altered=copy.deepcopy(result);altered['handoff_sha256']='another';self.assertFalse(compare(result,altered)['same_recorded_inputs'])
    def test_source_change_visible_in_comparison(self):
        package=self.root/'package';package.mkdir();(package/'SKILL.md').write_text('revision: "test"',encoding='utf-8')
        first=manifest(package,self.lock,'slab','text');(package/'source.py').write_text('changed')
        second=manifest(package,self.lock,'slab','text');self.assertIn('skill.source_sha256',compare(first,second)['differences'])
    def test_numbered_output_does_not_overwrite(self):
        first=new_output(self.root,'bunker');first.write_bytes(b'original')
        second=new_output(self.root,'bunker');self.assertNotEqual(first,second);self.assertEqual(first.read_bytes(),b'original')
    def test_output_traversal_rejected(self):
        with self.assertRaises(ValueError):new_output(self.root,'../skill')
    def test_cleanup_only_unchanged_owned_files(self):
        temp=new_temporary(self.root);owned=temp/'guide.txt';owned.write_text('guide')
        record=owned_record(temp,owned);self.assertEqual(cleanup_plan(temp,[record],self.image),[str(owned)])
        owned.write_text('user edit')
        with self.assertRaisesRegex(ValueError,'changed'):cleanup_plan(temp,[record],self.image)
    def test_cleanup_cannot_escape_run(self):
        temp=new_temporary(self.root)
        with self.assertRaisesRegex(ValueError,'escapes'):cleanup_plan(temp,[{'relative_path':'../final.png','sha256':'x'}],self.image)
    def test_cleanup_needs_verified_final(self):
        temp=new_temporary(self.root);self.image.write_bytes(b'broken')
        with self.assertRaises(Exception):cleanup_plan(temp,[],self.image)


if __name__=='__main__':unittest.main()
