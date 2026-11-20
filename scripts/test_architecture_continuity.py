import copy,tempfile,unittest
from pathlib import Path
import architecture_continuity as a
import repair_cycle as r

def fixture():
    return {'architecture':{'representation':'complete','enclosure':'Wall with door','roof_wall_junctions':'Roof on piers','openings':[{'kind':'door','boundary':'Wall jambs','reason':'Entry'}],'routes':'Entry to hall',
      'design':{'primary':'beam','selected_reason':'Clear supported hall','rejected_alternative':'Detached portal obscures access','elements':[
        {'id':'ground','role':'ground','extent':'Site','junction':'Terrain','hosts':[]},
        {'id':'left','role':'structure','extent':'Left pier','junction':'Footing','hosts':['ground']},
        {'id':'right','role':'structure','extent':'Right pier','junction':'Footing','hosts':['ground']},
        {'id':'beam','role':'structure','extent':'Hall span','junction':'Seats on piers','hosts':['left','right'],'spanning':True,'supports':['left','right']}]}}}

class ArchitectureTests(unittest.TestCase):
    def test_valid_design(self):a.validate(fixture(),'Draw hall');self.assertIn('architecture:design',a.keys(fixture()))
    def test_unrequested_cut(self):
        p=fixture();p['architecture'].update(representation='section',cut_boundary='roof')
        with self.assertRaises(ValueError):a.validate(p,'Draw hall')
    def test_missing_opening_boundary(self):
        p=fixture();p['architecture']['openings'][0].pop('boundary')
        with self.assertRaises(ValueError):a.validate(p,'Draw')
    def test_orphan_structure(self):
        p=fixture();p['architecture']['design']['elements'][1]['hosts']=['beam']
        p['architecture']['design']['elements'][2]['hosts']=['beam']
        with self.assertRaises(ValueError):a.validate(p,'Draw')
    def test_unknown_support(self):
        p=fixture();p['architecture']['design']['elements'][-1]['supports']=['left','missing']
        with self.assertRaises(ValueError):a.validate(p,'Draw')
    def test_repair_requires_changed_artifact_and_all_issues(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'a.txt';f.write_text('broken')
            rec=r.record(t,f,[dict(id='entry',component='door',observed='blocked',target='open',action='remove infill')])
            with self.assertRaises(ValueError):r.resolve(rec,f,{'entry':dict(status='resolved',evidence='claim')})
            f2=Path(t)/'b.txt';f2.write_text('fixed')
            with self.assertRaises(ValueError):r.resolve(rec,f2,{})
            self.assertTrue(r.resolve(rec,f2,{'entry':dict(status='resolved',evidence='opening inspected')}).exists())
