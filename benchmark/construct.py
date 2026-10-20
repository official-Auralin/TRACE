"""Optional standalone dataset constructor. Outputs only machine/trace/target.

Does not import the board/compiler/runtime. A fixed seed fixes the records.
Structural strata are sampling settings, not an empirically calibrated scale.
"""
import argparse
import json
from pathlib import Path
import random
import sys
from .core import canonical,digest,simulate,validate_item
from .game import bad_root

SEED=20261019


def records(count, states, inputs, horizon, seed, split='test', family='random', seen=None,
            temporal=False,max_attempts=100000):
    if any(type(v) is not int or v<1 for v in (count,states,inputs,horizon)):
        raise ValueError('positive finite dimensions/count required')
    rng=random.Random(seed);seen=set() if seen is None else seen
    if temporal and horizon<2:raise ValueError('earlier-round dependence requires at least two rounds')
    if temporal and states==1 and horizon>1:raise ValueError('one-state machines cannot meet the requested earlier-round dependence filter')
    if count>(2*states)**(states*(1<<inputs)):raise ValueError('requested distinct-machine count exceeds the finite source space')
    produced=attempts=0
    while produced<count:
        attempts+=1
        if max_attempts is not None and attempts>max_attempts:
            raise TimeoutError('sampling attempt budget exhausted; increase --max-attempts or revise the sampling parameters')
        machine={'inputs':[chr(65+r) if r<26 else f'I{r}' for r in range(inputs)],
            'states':states,'initial':0,'transitions':[
                [{'next':rng.randrange(states),'output':rng.randrange(2)} for _ in range(1<<inputs)] for _ in range(states)]}
        identity=digest(machine)
        if identity in seen:continue
        observed=[[rng.randrange(2) for _ in range(inputs)] for _ in range(horizon)]
        if simulate(machine,observed)['outputs'][-1]!=1:continue
        item={'machine':machine,'observed':observed,'target_step':horizon-1}
        validate_item(item)
        # If last-round values alone do not guarantee the target, every valid
        # explanation must contain an earlier cell. This needs no all-answer scan.
        if temporal and horizon>1 and not bad_root(item,range((horizon-1)*inputs,horizon*inputs)):continue
        if temporal and not bad_root(item,[]):continue
        seen.add(identity);produced+=1
        yield {'id':'m-'+digest(item)[:20],'split':split,'family':family,**item}


def release(seed=SEED,max_attempts=100000):
    seen=set()
    # Eight sampling strata, 128 test items each, interleaved so the first 64
    # contain eight per stratum. Other splits use independent random streams.
    strata=[(q,m,h) for q in (2,4) for m in (2,3) for h in (3,5)]
    for split,total,offset in (('tutorial',16,100),('pilot',32,200),('development',256,300),('test',1024,400)):
        streams=[]
        for j,(q,m,h) in enumerate(strata):
            if split=='tutorial':q,m,h=2,1,2+j%2
            if split=='pilot':q,m,h=2,2,3
            streams.append(records(total//8,q,m,h,seed+offset+j,split,f'q{q}-m{m}-h{h}',seen,temporal=True,max_attempts=max_attempts))
        for _ in range(total//8):
            for stream in streams:yield next(stream)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True);p.add_argument('--release',action='store_true')
    p.add_argument('--count',type=int,default=1);p.add_argument('--states',type=int,default=2)
    p.add_argument('--inputs',type=int,default=3);p.add_argument('--horizon',type=int,default=3)
    p.add_argument('--seed',type=int,default=SEED)
    p.add_argument('--temporal',action='store_true',help='require an explanation to use an earlier-round cell')
    p.add_argument('--max-attempts',type=int,default=100000,help='operator sampling budget; 0 means unlimited')
    a=p.parse_args();path=Path(a.output)
    if path.exists():raise SystemExit('Output exists; choose a new dataset path')
    path.parent.mkdir(parents=True,exist_ok=True)
    if a.max_attempts<0:p.error('--max-attempts must be nonnegative')
    iterator=release(a.seed,a.max_attempts or None) if a.release else records(a.count,a.states,a.inputs,a.horizon,a.seed,temporal=a.temporal,max_attempts=a.max_attempts or None)
    count=0
    try:
        with path.open('w') as out:
            for row in iterator:out.write(canonical(row)+'\n');count+=1
    except (TimeoutError,ValueError) as error:
        print(json.dumps({'status':'INCOMPLETE' if isinstance(error,TimeoutError) else 'ERROR','records_written':count,'error':str(error)}),file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({'status':'PASS','records':count,'seed':a.seed,'output':str(path),'scope':'valid generated data; compile separately for a playable certified package'}))

if __name__=='__main__':main()
