"""Create a shuffled, balanced anonymous human-panel assignment schedule before trials."""
import argparse,json,random,uuid
from pathlib import Path
from .runtime import load_package

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--coverage',type=int,default=8);p.add_argument('--seed',type=int,default=1729);p.add_argument('--condition',choices=['reasoning','probe','both'],default='reasoning');p.add_argument('--output',required=True)
    p.add_argument('--dataset',help='Compiled package directory; defaults to data/')
    a=p.parse_args()
    if a.coverage<1:p.error('Coverage must be positive')
    output=Path(a.output)
    if output.exists():p.error('Use a new schedule path')
    _,_,manifest,forms=load_package(a.dataset);conditions=['reasoning','probe'] if a.condition=='both' else [a.condition]
    panel={name:form for name,form in forms.items() if form.get('human_panel',False)}
    if not panel:p.error('The package has no designated human-panel forms')
    item_ids=[iid for form in panel.values() for iid in form['item_ids']]
    if len(set(item_ids))!=len(item_ids):p.error('Balanced allocation requires disjoint panel forms')
    rows=[{'form_id':name,'condition':condition,'rotation':rep%len(form['item_ids'])} for name,form in panel.items() for condition in conditions for rep in range(a.coverage)]
    random.Random(a.seed).shuffle(rows)
    schedule_id=uuid.uuid4().hex[:12]
    for i,r in enumerate(rows):r['allocation_id']=f'{schedule_id}-A{i+1:04d}';r['participant_id']=f'{schedule_id}-H{i+1:04d}'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps({'schedule_id':schedule_id,'dataset_sha256':manifest['dataset_sha256'],'forms_sha256':manifest['forms_sha256'],'seed':a.seed,'coverage':a.coverage,'rotation_balance':'Position counts differ by at most one; exact balance when coverage is divisible by form length.','status':'PLANNED assignments; no enrollment implied','assignments':rows},indent=2)+'\n')
    print(f'{len(rows)} planned participants; {a.coverage} judgments per panel item per condition; {output}')
if __name__=='__main__':main()
