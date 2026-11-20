import tempfile,unittest,zipfile
from pathlib import Path
from build_package import build,verify,manifest


class PackageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'skill';self.root.mkdir()
        for name in ('SKILL.md','README.md','requirements.txt','kit/__init__.py','evals/evals.json','evals/rubric.json','references/art-direction.md'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original source',encoding='utf-8')
    def tearDown(self):self.temp.cleanup()
    def test_source_zip_equal_and_nonoverwrite(self):
        out=self.base/'release.zip';report=build(self.root,out)
        self.assertTrue(report['source_and_zip_identical']);self.assertEqual(report['files'],7)
        with self.assertRaises(FileExistsError):build(self.root,out)
    def test_image_blocks_packaging(self):
        (self.root/'reference.png').write_bytes(b'art')
        with self.assertRaisesRegex(ValueError,'artifact'):build(self.root,self.base/'release.zip')
    def test_tampered_zip_rejected(self):
        out=self.base/'release.zip';expected=manifest(self.root);build(self.root,out)
        with zipfile.ZipFile(out,'a') as z:z.writestr('scene-layout-forge/unexpected.txt','new')
        with self.assertRaisesRegex(ValueError,'differ'):verify(out,expected)
    def test_package_cannot_write_inside_skill(self):
        with self.assertRaisesRegex(ValueError,'outside skill'):build(self.root,self.root/'release.zip')


if __name__=='__main__':unittest.main()
