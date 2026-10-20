"""Sensitivity analysis for sample planning, never power or observed trial results.
Simulates a designated fixed panel with shared participant ability within each
form. Reports central 95% sampling ranges for the agent-minus-human estimate under
explicit hypothetical probabilities; this is not a calibrated bootstrap coverage test.
"""
import argparse,json,math,random,statistics
from pathlib import Path
from .runtime import load_package
from .analyze import percentile

def simulate_plan(repetitions=1000,seed=1729,coverages=(8,12,16),dataset=None):
    _,_,manifest,forms=load_package(dataset);panel=[f['item_ids'] for f in forms.values() if f.get('human_panel',False)]
    total_items=sum(map(len,panel))
    if not total_items:raise ValueError('Sample planning requires a designated panel')
    if len({iid for form in panel for iid in form})!=total_items:raise ValueError('Sample planning requires disjoint panel forms')
    if repetitions<1 or not coverages or any(type(n) is not int or n<1 for n in coverages):raise ValueError('Simulation and coverage counts must be positive')
    offsets={len(form):[0.] if len(form)==1 else [-.75+1.5*j/(len(form)-1) for j in range(len(form))] for form in panel}
    rng=random.Random(seed);scenarios=[]
    for coverage in coverages:
        for human_probability in (.25,.5,.75):
            for ability_sd in (0.,1.):
                gaps=[]
                for _ in range(repetitions):
                    human_total=agent_total=0.
                    for form in panel:
                        human=[0]*len(form);agent=[0]*len(form)
                        for participant in range(coverage):
                            ability=rng.gauss(0,ability_sd)
                            for j in range(len(form)):
                                offset=offsets[len(form)][j]
                                probability=1/(1+math.exp(-(math.log(human_probability/(1-human_probability))+offset+ability)))
                                human[j]+=rng.random()<probability
                        for repeat in range(5):
                            for j in range(len(form)):agent[j]+=rng.random()<.5
                        human_total+=sum(human)/coverage;agent_total+=sum(agent)/5
                    gaps.append(100*(agent_total-human_total)/total_items)
                low,high=percentile(gaps,.025),percentile(gaps,.975)
                scenarios.append({'human_judgments_per_item':coverage,'usable_humans_per_condition':len(panel)*coverage,
                                  'human_probability_at_zero_offsets':human_probability,'participant_logit_sd':ability_sd,
                                  'agent_probability':.5,'agent_repetitions':5,'simulated_gap_mean_pp':statistics.mean(gaps),
                                  'central95_sampling_range_pp':[low,high],'central95_width_pp':high-low})
    return {'status':'PLANNING SIMULATION — NOT TRIAL DATA','dataset_sha256':manifest['dataset_sha256'],'panel_items':total_items,
            'monte_carlo_studies_per_scenario':repetitions,'seed':seed,'fixed_item_logit_offsets_by_form_size':offsets,
            'limitations':'Assumed response probabilities and clustering, no attrition, independent agent calls, no calibration to human data. Widths describe hypothetical sampling distributions, not guaranteed confidence-interval coverage, effect detection or achieved power. Reassess assumptions after the pilot and preregister the chosen design.',
            'inference_gate':'Confirmatory use requires registration and review of fixed eligibility/independent cluster assumptions. Bootstrap intervals remain exploratory.',
            'hoeffding_calibration':calibrate_bounds(repetitions,seed+1,form_sizes=tuple(map(len,panel))),
            'scenarios':scenarios}

def calibrate_bounds(repetitions=1000,seed=1730,form_sizes=(4,)*16,human_coverage=8,agent_n=5):
    """Hypothetical coverage stress check; Hoeffding's bound supplies the guarantee
    under its assumptions. Simulations do not validate real recruitment/independence.
    """
    if repetitions<1 or not form_sizes or any(type(n) is not int or n<1 for n in form_sizes) or human_coverage<1 or agent_n<1:raise ValueError('Calibration counts must be positive')
    rng=random.Random(seed);results=[];panel_items=sum(form_sizes);human_n=human_coverage*len(form_sizes)
    human_sizes=[size for size in form_sizes for _ in range(human_coverage)]
    human_weights=[size/(panel_items*human_coverage) for size in human_sizes]
    for human_p,agent_p in ((.1,.1),(.25,.5),(.5,.5),(.9,.9)):
        for within_cluster in ('independent items','perfect correlation'):
            covered=0
            radius=math.sqrt(math.log(40)*(sum(w*w for w in human_weights)+1/agent_n)/2)
            for _ in range(repetitions):
                if within_cluster=='perfect correlation':
                    human=sum(weight*(rng.random()<human_p) for weight in human_weights)
                    agent=sum(rng.random()<agent_p for _ in range(agent_n))/agent_n
                else:
                    human=sum(rng.random()<human_p for size in human_sizes for _ in range(size))/(panel_items*human_coverage)
                    agent=sum(rng.random()<agent_p for _ in range(agent_n*panel_items))/(agent_n*panel_items)
                covered+=abs((agent-human)-(agent_p-human_p))<=radius
            results.append({'human_p':human_p,'agent_p':agent_p,'dependence_within_cluster':within_cluster,
                'human_clusters':human_n,'agent_run_clusters':agent_n,'radius_pp':100*radius,
                'empirical_coverage':covered/repetitions,'covered':covered,'simulated_studies':repetitions})
    return {'status':'SYNTHETIC CALIBRATION ONLY; no participant or provider evidence','seed':seed,
        'panel_items':panel_items,'form_sizes':list(form_sizes),
        'assumptions':'Fixed complete assignment; independent clusters; arbitrary dependence within clusters. Agent repetitions are clustered across the complete panel.',
        'scenarios':results}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--simulations',type=int,default=1000);p.add_argument('--seed',type=int,default=1729);p.add_argument('--output',required=True);p.add_argument('--dataset',help='Compiled package directory; defaults to data/');a=p.parse_args()
    if a.simulations<100:p.error('Use at least 100 simulated studies')
    path=Path(a.output)
    if path.exists():p.error('Use a new output path')
    result=simulate_plan(a.simulations,a.seed,dataset=a.dataset);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(path),'scenarios':len(result['scenarios']),'status':result['status']}))
if __name__=='__main__':main()
