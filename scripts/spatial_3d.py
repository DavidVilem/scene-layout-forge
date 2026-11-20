"""Independent image reconstruction and design-first snapshots; JSON inputs, retained history."""
import argparse,json
from kernel3d.workflow import start,snapshot,calibrate,reconstruct,deliver_glb,read

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('start');a.add_argument('--project',required=True);a.add_argument('--mode',choices=['design_first','single_image'],required=True);a.add_argument('--brief',required=True);a.add_argument('--source')
 a=sub.add_parser('snapshot');a.add_argument('--run',required=True);a.add_argument('--spec',required=True);a.add_argument('--camera',required=True);a.add_argument('--evidence',required=True);a.add_argument('--previous')
 a=sub.add_parser('calibrate');a.add_argument('--run',required=True);a.add_argument('--landmarks',required=True)
 a=sub.add_parser('reconstruct');a.add_argument('--run',required=True);a.add_argument('--snapshot',required=True)
 a=sub.add_parser('deliver-glb');a.add_argument('--snapshot',required=True);a.add_argument('--job',required=True)
 a=p.parse_args()
 if a.command=='start':result=start(a.project,a.mode,a.brief,a.source)
 elif a.command=='snapshot':result=snapshot(a.run,read(a.spec),read(a.camera),read(a.evidence),a.previous)
 elif a.command=='calibrate':result=calibrate(a.run,**read(a.landmarks))
 elif a.command=='reconstruct':result=reconstruct(a.run,a.snapshot)
 else:result=deliver_glb(a.snapshot,a.job)
 print(json.dumps(result,default=str,ensure_ascii=False))

if __name__=='__main__':main()
