import unittest,math
from reconstruction_geometry import mesh_for,component
from access_network import inspect
class GeneralFormsTests(unittest.TestCase):
 def test_lofts_for_vehicle_shell_duct_and_tower(self):
  for scale in (1,.5,2):
   rings=[[[scale*math.cos(i*math.pi/4)*(1+.1*z),z,scale*math.sin(i*math.pi/4)] for i in range(8)] for z in (0,1,4)]
   self.assertGreater(len(mesh_for({'type':'loft','rings':rings})),30)
 def test_bad_rings_rejected(self):
  with self.assertRaises(ValueError):mesh_for({'type':'loft','rings':[[[0,0,0],[1,0,0],[0,1,0]],[[0,0,1],[1,0,1]]]})
 def test_nonplanar_rejected(self):
  with self.assertRaises(ValueError):mesh_for({'type':'loft','rings':[[[0,0,0],[1,0,0],[1,1,0],[0,1,.1]],[[0,0,1],[1,0,1],[1,1,1],[0,1,1]]]})
 def scene(self,gap=0):
  return {'parts':[component({'id':name,'shapes':[{'type':'box','at':[x,0,0],'size':[1,2,.25]}]}) for name,x in [('a',0),('b',1+gap)]]}
 def network(self):return {'entry':'start','targets':['end'],'nodes':[{'id':'start','point':[.1,1,.25]},{'id':'end','point':[1.9,1,.25]}],'links':[{'from':'start','to':'end','supports':['a','b']}]}
 def test_continuous_floor_and_reachability(self):self.assertEqual(inspect(self.network(),self.scene())['status'],'passed')
 def test_tiny_gap_not_missed_by_sampling(self):
  with self.assertRaisesRegex(ValueError,'Unsupported'):inspect(self.network(),self.scene(.002))
 def test_unreachable_platform_rejected(self):
  n=self.network();n['links']=[]
  with self.assertRaisesRegex(ValueError,'Unreachable'):inspect(n,self.scene())
 def test_floating_route_rejected(self):
  n=self.network()
  for p in n['nodes']:p['point'][2]=.3
  with self.assertRaisesRegex(ValueError,'Unsupported'):inspect(n,self.scene())
