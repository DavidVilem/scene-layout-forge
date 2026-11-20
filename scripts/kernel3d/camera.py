"""Perspective camera fitting from explicit 3D/2D landmarks. No hidden geometry recovery."""
import numpy as np

def project(points,camera,aspect):
 eye=np.asarray(camera['eye'],float);target=np.asarray(camera['target'],float)
 if eye.shape!=(3,) or target.shape!=(3,) or not np.isfinite([eye,target]).all() or not np.isfinite(aspect) or aspect<=0 or not 0<camera['fov']<180:raise ValueError('Finite camera and positive aspect required')
 if np.linalg.norm(target-eye)<1e-8 or np.linalg.norm(np.cross(target-eye,[0,0,1]))<1e-8:raise ValueError('Degenerate camera orientation')
 f=target-eye;f/=np.linalg.norm(f);right=np.cross(f,[0.,0.,1.]);right/=np.linalg.norm(right);up=np.cross(right,f)
 p=np.asarray(points,float)-eye;z=p@f
 if np.any(z<=1e-5):raise ValueError('Landmark behind camera')
 scale=np.tan(np.radians(camera['fov'])/2)
 return np.column_stack((.5+(p@right)/(2*z*scale*aspect),.5-(p@up)/(2*z*scale)))

def fit(world,image,initial,aspect,iterations=120):
 w=np.asarray(world,float);uv=np.asarray(image,float)
 if w.ndim!=2 or w.shape[1]!=3 or len(w)<6 or uv.shape!=(len(w),2) or not np.isfinite(w).all() or not np.isfinite(uv).all():raise ValueError('Six finite paired landmarks required')
 if np.linalg.matrix_rank(w-w.mean(axis=0))<3:raise ValueError('Depth-varying landmarks required; planar-only calibration is ambiguous')
 if np.any(uv<0) or np.any(uv>1):raise ValueError('Normalized image coordinates required')
 def cam(x):return {'projection':'perspective','eye':x[:3].tolist(),'target':x[3:6].tolist(),'fov':float(np.clip(x[6],12,100)),'rationale':'Fitted to explicit observed landmarks; hidden geometry is not estimated'}
 x=np.array(initial['eye']+initial['target']+[initial['fov']],float)
 def residual(v):return (project(w,cam(v),aspect)-uv).ravel()
 r=residual(x);before=float(np.sqrt(np.mean(r*r)));lam=.001
 for _ in range(iterations):
  jac=np.zeros((len(r),7))
  for j in range(7):
   step=1e-5*max(1,abs(x[j]));y=x.copy();y[j]+=step;jac[:,j]=(residual(y)-r)/step
  delta=np.linalg.solve(jac.T@jac+lam*np.eye(7),-jac.T@r)
  y=x+delta;y[6]=np.clip(y[6],12,100)
  try:new=residual(y)
  except ValueError:lam*=10;continue
  if new@new<r@r:x,r=y,new;lam=max(lam/2,1e-9)
  else:lam=min(lam*8,1e6)
  if np.linalg.norm(delta)<1e-8:break
 return {'camera':cam(x),'rms_before':before,'rms_after':float(np.sqrt(np.mean(r*r))),'per_landmark':np.linalg.norm(r.reshape(-1,2),axis=1).tolist(),'scope':'Reprojection of declared landmarks, not silhouette or semantic fidelity'}
