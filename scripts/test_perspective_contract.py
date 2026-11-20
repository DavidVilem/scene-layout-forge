import copy,tempfile,unittest
from pathlib import Path
from PIL import Image
import perspective_contract as pc
import illustration_workflow as w
import color_workflow as c
from test_illustration_workflow import plan

def fixture():
    p=plan()
    p['perspective_contract']={'projection':'perspective','camera':'one oblique camera','horizon':'unknown; inspect horizontal families','groups':[{'id':'boat','orientation':'rotated from quay','families':{'length':'roof and sill straight edges'},'exceptions':'curved bow'}],'relationships':[]}
    return p

class PerspectiveContractTests(unittest.TestCase):
    def test_legacy_readable(self):self.assertEqual(pc.keys(plan()),set())
    def test_rotated_group_valid(self):pc.validate(fixture()['perspective_contract'])
    def test_unknown_relation_rejected(self):
        p=fixture()['perspective_contract'];p['relationships']=[{'groups':['boat','missing'],'alignment':'parallel','reason':'test'}]
        with self.assertRaises(ValueError):pc.validate(p)
    def test_duplicate_rejected(self):
        p=fixture()['perspective_contract'];p['groups']*=2
        with self.assertRaises(ValueError):pc.validate(p)
    def test_uncertain_short_edge_allowed(self):
        p=fixture();obs={k:{'status':'uncertain','evidence':['Cropped edge; insufficient support']} for k in pc.keys(p)};pc.review(p,obs)
    def test_generic_review_rejected(self):
        p=fixture()
        with self.assertRaises(ValueError):pc.review(p,{k:{'status':'visible_correct','notes':'clear depth'} for k in pc.keys(p)})
    def test_one_edge_not_a_pass(self):
        p=fixture();obs={k:{'status':'visible_correct','evidence':['one line']} for k in pc.keys(p)}
        with self.assertRaises(ValueError):pc.review(p,obs)
    def test_workflow_requires_group_review(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=fixture();a=w.prepare(root,'boat','Draw boat',p)
            src=root/'s.png';Image.new('RGB',(24,16),'white').save(src)
            im=w.retain(a,src,w.read(a/'request.json'))
            obs={k:{'status':'visible_correct','notes':'Synthetic fixture'} for k in set(w.BASE_REVIEW)|set(p['relationships'])}
            with self.assertRaises(ValueError):w.review(a,im,obs)
            obs.update({k:{'status':'uncertain','notes':'Synthetic uncertainty','evidence':['Short roof edge; no reliable intersection']} for k in pc.keys(p)})
            rv=w.review(a,im,obs);w.accept(a,im,rv,root/'ilustrada.png')
            c.prepare(a,root/'ilustrada.png')

    def test_unresolved_perspective_cannot_be_colored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=fixture();a=w.prepare(root,'boat','Draw boat',p)
            src=root/'s.png';Image.new('RGB',(24,16),'white').save(src)
            im=w.retain(a,src,w.read(a/'request.json'))
            obs={k:{'status':'visible_correct','notes':'Synthetic fixture'} for k in set(w.BASE_REVIEW)|set(p['relationships'])}
            obs.update({k:{'status':'uncertain','notes':'Synthetic fixture','evidence':['Short edge']} for k in pc.keys(p)})
            obs['perspective:group:boat']['status']='visible_error'
            rv=w.review(a,im,obs)
            for i in range(2):
                req=w.correction(a,im,rv,'Synthetic local correction '+str(i))
                im=w.retain_correction(a,src,req);rv=w.review(a,im,obs)
            w.accept(a,im,rv,root/'ilustrada.png')
            with self.assertRaisesRegex(ValueError,'Known perspective defect'):c.prepare(a,root/'ilustrada.png')

if __name__=='__main__':unittest.main()
