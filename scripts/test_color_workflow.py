import tempfile,unittest
from pathlib import Path
from PIL import Image
import illustration_workflow as w
import color_workflow as c
from test_illustration_workflow import plan

class ColorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        a=w.prepare(self.root,'scene','Draw a scene.',plan());self.attempt=a
        src=self.root/'source.png';Image.new('RGB',(24,16),'gray').save(src)
        im=w.retain(a,src,w.read(a/'request.json'))
        obs={k:{'status':'visible_correct','notes':'Synthetic fixture only'} for k in (*w.BASE_REVIEW,'wall_mount')}
        rv=w.review(a,im,obs);self.illustrated=self.root/'output/scene-01/ilustrada.png'
        w.accept(a,im,rv,self.illustrated)
        self.color=self.root/'color.png';Image.new('RGB',(24,16),'steelblue').save(self.color)
    def tearDown(self):self.tmp.cleanup()
    def job(self):return c.prepare(self.attempt,self.illustrated)
    def reviewed(self,job,image=None):
        c.retain(job,image or self.color,w.read(job/'request.json'))
        return c.review(job,{k:{'status':'preserved','notes':'Synthetic workflow fixture, not a visual evaluation'} for k in c.KEYS})
    def test_two_named_files_and_original_preserved(self):
        before=self.illustrated.read_bytes();job=self.job();rv=self.reviewed(job);result=c.accept(job,rv)
        self.assertEqual(Path(result['coloreada']).name,'coloreada.png')
        self.assertEqual(self.illustrated.read_bytes(),before)
        self.assertEqual({p.name for p in self.illustrated.parent.iterdir()},{'ilustrada.png','coloreada.png'})
    def test_no_overwrite(self):
        job=self.job();rv=self.reviewed(job);c.accept(job,rv)
        with self.assertRaises(FileExistsError):c.accept(job,rv)
    def test_known_architecture_failure_blocks_coloring(self):
        import json
        selected=w.read(next(self.attempt.glob('selected-*.json')))
        review=Path(selected['review']);record=w.read(review)
        record['observations']['architecture:design']={'status':'visible_error','notes':'Synthetic unresolved detached portal'}
        review.write_text(json.dumps(record),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'architecture defect'):self.job()
    def test_source_change_rejected(self):
        job=self.job();Image.new('RGB',(24,16),'black').save(self.illustrated)
        with self.assertRaises(ValueError):c.retain(job,self.color,w.read(job/'request.json'))
    def test_request_tamper_rejected(self):
        job=self.job();(job/'request.json').write_text('{}')
        with self.assertRaises(ValueError):c.retain(job,self.color,{})
    def test_missing_comparison_rejected(self):
        job=self.job();c.retain(job,self.color,w.read(job/'request.json'))
        with self.assertRaises(ValueError):c.review(job,{})
    def test_changed_geometry_rejected(self):
        job=self.job();self.reviewed(job)
        obs={k:{'status':'preserved','notes':'fixture'} for k in c.KEYS}
        obs['connections']={'status':'changed','notes':'pipe endpoint moved'}
        rv=c.review(job,obs)
        with self.assertRaises(ValueError):c.accept(job,rv)
    def test_same_image_not_color(self):
        job=self.job();rv=self.reviewed(job,self.illustrated)
        with self.assertRaises(ValueError):c.accept(job,rv)
    def test_size_change_rejected(self):
        Image.new('RGB',(48,16),'steelblue').save(self.color)
        job=self.job();rv=self.reviewed(job)
        with self.assertRaises(ValueError):c.accept(job,rv)
    def test_correction_budget(self):
        job=self.job();self.reviewed(job)
        for _ in range(2):
            job=c.prepare(self.attempt,self.illustrated,previous=job,correction='Preserve pipe linework');self.reviewed(job)
        with self.assertRaises(ValueError):c.prepare(self.attempt,self.illustrated,previous=job,correction='again')

if __name__=='__main__':unittest.main()
