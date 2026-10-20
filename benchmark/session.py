"""Researcher-only session creation, form inventory and raw-event export."""
import argparse,json
from pathlib import Path
from .runtime import StudyStore,load_package
from .core import MODES

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('create');a.add_argument('--db',default='runs/study.sqlite3');a.add_argument('--cohort',choices=['human','agent','baseline'],required=True)
    a.add_argument('--participant',required=True);a.add_argument('--split',required=True);a.add_argument('--form',required=True)
    a.add_argument('--condition',choices=['reasoning','probe'],default='reasoning');a.add_argument('--mode',choices=MODES,default='explanation');a.add_argument('--rotation',type=int,default=0)
    a.add_argument('--seconds',type=float,default=480,help='Positive finite per-item time budget')
    a.add_argument('--probes',type=int,default=8,help='Nonnegative probe-arm query budget')
    a.add_argument('--metadata',help='JSON file for pinned agent metadata');a.add_argument('--base-url',default='http://127.0.0.1:8765')
    a=sub.add_parser('export');a.add_argument('--db',default='runs/study.sqlite3');a.add_argument('--output',required=True)
    a=sub.add_parser('technical-error');a.add_argument('--db',default='runs/study.sqlite3');a.add_argument('--token',required=True);a.add_argument('--reason',required=True)
    a=sub.add_parser('forms');a.add_argument('--split',default='test');a.add_argument('--human-panel',action='store_true')
    for parser in sub.choices.values():parser.add_argument('--dataset',help='Compiled package directory; defaults to data/')
    args=p.parse_args()
    if args.command=='forms':
        forms=load_package(args.dataset)[3];print(json.dumps({k:v for k,v in forms.items() if v['split']==args.split and (not args.human_panel or v.get('human_panel',False))},indent=2));return
    store=StudyStore(args.db,dataset=args.dataset)
    if args.command=='export':result=store.export(args.output)
    elif args.command=='technical-error':
        store.technical_error(args.token,args.reason);result={'recorded':True}
    else:
        metadata=json.loads(Path(args.metadata).read_text()) if args.metadata else {}
        result=store.create(args.cohort,args.participant,args.split,args.form,args.condition,args.mode,args.rotation,metadata,seconds=args.seconds,probes=args.probes)
        result['participant_url']=args.base_url+'/#token='+result['token']
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
