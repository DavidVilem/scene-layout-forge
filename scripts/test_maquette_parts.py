import unittest
from maquette_parts import *
from reconstruction_geometry import component,mesh_for
from maquette_quality import triangle_box
import numpy as np
class ConstructionFamiliesTests(unittest.TestCase):
 def test_real_door_not_painted_rectangle(self):
  shapes=wall_openings(6,3,.2,[(2,0,2,2.4)])
  triangles=[f for s in shapes for f in mesh_for(s)]
  self.assertFalse(any(triangle_box(np.array(t),np.array([2.1,.01,.01]),np.array([3.9,.19,2.3])) for t in triangles))
 def test_invalid_opening(self):
  with self.assertRaises(ValueError):wall_openings(2,2,.1,[(1,1,2,2)])
 def test_build_all_families(self):
  for family in (window(3,2),pitched_roof(8,12,3,2),canopy(3,12,3),vehicle_shell(2,14,2.4)):
   for name,shapes in family.items():self.assertTrue(component({'id':name,'shapes':shapes})['parameters']['faces'])
 def test_glass_not_in_opaque_plane(self):
  a=window(3,2);self.assertEqual(len(a['glass']),9)
  self.assertTrue(all(s['size'][1]<.02 for s in a['glass']))
 def test_translation_keeps_input(self):
  a=[box([0,0,0],[1,1,1])];b=translated(a,[2,3,4]);self.assertEqual(a[0]['at'],[0,0,0]);self.assertEqual(b[0]['at'],[2,3,4])

 def test_pavilion_example_has_real_supported_access(self):
  import importlib.util
  from pathlib import Path
  from reconstruction_kernel import compile_spec
  path=Path(__file__).resolve().parents[1]/'examples/presentation-maquette/build.py'
  module_spec=importlib.util.spec_from_file_location('pavilion',path)
  module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
  scene,config,checks=compile_spec(module.specification())
  self.assertEqual(checks['access_network']['status'],'passed')
  self.assertEqual(checks['quality']['status'],'passed_applicable')
  self.assertGreater(len(scene['parts']),15)
