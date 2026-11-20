"""Public geometry API; shared implementation remains in scripts for compatibility."""
from pathlib import Path
import sys

_implementation = str(Path(__file__).resolve().parents[1] / 'scripts')
if _implementation not in sys.path:
    sys.path.insert(0, _implementation)
from scene_model import make_part, validate, validation_report
from design_intent import DesignIntent
from design_variants import generate_candidates, choose_candidate, verify_selection
from assembly_model import RigidTransform, compose_assembly, cut_host, compile_cutaway
from connected_plant import fixture as twin_vessels
from factory import factory
from highrise import highrise
from render_scene import build, Renderer
from generate_design import generate
from route_geometry import rounded_route
from visual_contract import VisualPlan,ContextPlan,DetailBudget,LightMaterialPlan,SubjectFraming,compile_visual_contract
from useful_camera import fit_camera,select_useful_view,CameraSelectionError
from finish_contract import freeze,compile_handoff
from pixel_review import create_review

__all__ = ['make_part', 'validate', 'twin_vessels', 'factory', 'highrise',
           'build', 'Renderer', 'generate', 'rounded_route', 'validation_report',
           'DesignIntent', 'generate_candidates', 'choose_candidate', 'verify_selection',
           'RigidTransform', 'compose_assembly', 'cut_host', 'compile_cutaway',
           'VisualPlan','ContextPlan','DetailBudget','LightMaterialPlan','SubjectFraming',
           'compile_visual_contract','fit_camera','select_useful_view','CameraSelectionError',
           'freeze','compile_handoff','create_review']
