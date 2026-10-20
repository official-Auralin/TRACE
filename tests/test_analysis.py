import copy,hashlib,json,math,tempfile,unittest
from pathlib import Path
from benchmark.analyze import analyze,AnalysisError,macro,load_trials,cluster_bound,configuration,REGISTRATION_ASSUMPTIONS
from benchmark.core import grade,PROTOCOL_VERSION,digest
from benchmark.paths import ROOT
from benchmark.game import solve
from benchmark.runtime import load_package
from benchmark.plan_sample import calibrate_bounds

class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,body,cls.manifest,cls.forms=load_package();cls.items=body['items']
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def fixture(self):
        rows=[];files={'fixture':'a'*64};provenance={'files_sha256':files,'source_sha256':digest(files),'instructions_sha256':'b'*64}
        meta={'system_id':'fixture','provider':'mock','model_snapshot':'fixture-snapshot','generation':{'max_completion_tokens':100},'registration_id':'fixture-only','adapter_files_sha256':{'fixture':'a'*64},'batch_id':'fixture-batch'}
        for name,form in self.forms.items():
            if not form['human_panel']:continue
            for cohort in ('human','agent'):
                for rep in range(2):
                    for iid in form['item_ids']:
                        item=self.items[iid];answer={'cells':solve(item) if rep or cohort=='agent' else []};score=grade(item,answer)
                        participant=f'{cohort}-{name}-{rep}' if cohort=='human' else f'agent-run-{rep}'
                        rows.append(dict(record_type='trial',schema_version='trace.trial.v2',protocol_version=PROTOCOL_VERSION,dataset_sha256=self.manifest['dataset_sha256'],forms_sha256=self.manifest['forms_sha256'],session_id=f'{cohort}-{name}-{rep}',participant_id=participant,cohort=cohort,condition='reasoning',form_id=name,form_item_ids=form['item_ids'],mode='explanation',item_id=iid,family=item['family'],split='test',agent_metadata=meta.copy(),source_provenance=provenance,cell_count=(item['target_step']+1)*len(item['machine']['inputs']),status='submitted',duration_ms=100,probes_used=0,attempts_used=1,limits={'attempts':1,'seconds':480,'probes':0},response=answer,request_id=f'{cohort}-{name}-{rep}-{iid}',reason=None,**score))
        return rows
    def write(self,rows):
        path=self.root/'raw.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));return path
    def test_known_rates_gap_and_determinism(self):
        path=self.write(self.fixture());r=analyze([path],self.root/'a',count=100,seed=1);s=analyze([path],self.root/'b',count=100,seed=1)
        self.assertEqual(r,s);self.assertEqual(r['groups']['human / reasoning']['accuracy'],.5);self.assertEqual(r['groups']['agent:fixture / reasoning']['accuracy'],1);self.assertEqual(r['contrasts'][0]['gap_pp'],50)
        self.assertIsNotNone(r['contrasts'][0]['ci95_pp']);self.assertFalse(r['confirmatory_ready']);self.assertNotIn('cell_f1',r['groups']['human / reasoning'])
        bound=r['groups']['agent:fixture / reasoning']['conservative_cluster_bound'];self.assertEqual(bound['independent_clusters'],2);self.assertAlmostEqual(bound['sum_squared_cluster_ranges'],.5)
    def test_missing_items_not_silently_dropped(self):
        rows=self.fixture();rows=[r for r in rows if r['item_id']!=rows[0]['item_id']];r=analyze([self.write(rows)],self.root/'a',count=10)
        self.assertIsNone(r['groups']['human / reasoning']['accuracy']);self.assertIsNone(r['contrasts'][0]['gap_pp'])
    def test_reject_duplicates_versions_and_forged_scores(self):
        original=self.fixture()[:1];cases=[original*2]
        for key,value in [('dataset_sha256','bad'),('correct',True),('duration_ms',float('nan')),('probes_used',1),('protocol_version','trace-study-v1'),('request_id',None),('forms_sha256','bad')]:
            rows=copy.deepcopy(original);rows[0][key]=value;cases.append(rows)
        for rows in cases:
            with self.assertRaises(AnalysisError):load_trials([self.write(rows)],self.items,self.manifest,self.forms)
    def test_reject_model_configuration_drift(self):
        rows=[r for r in self.fixture() if r['cohort']=='agent'][:2]
        for key,value in [('model_snapshot','changed'),('generation',{'max_completion_tokens':200}),('provider','other')]:
            edited=copy.deepcopy(rows);edited[1]['agent_metadata'][key]=value
            with self.assertRaises(AnalysisError):load_trials([self.write(edited)],self.items,self.manifest,self.forms)
    def test_timeout_exclusion_and_incomplete_interval(self):
        rows=self.fixture();rows[0].update(status='timeout',attempts_used=0,correct=False,guarantee=False,prevention=False,minimality=False,valid_format=False,duration_ms=480000)
        rows[1].update(status='technical_error',attempts_used=0,correct=None,guarantee=None,prevention=None,minimality=None,valid_format=False,reason='fixture outage')
        r=analyze([self.write(rows)],self.root/'a',count=10);group=r['groups']['human / reasoning']
        self.assertEqual(group['included_trials'],127);self.assertEqual(group['disposition']['timeout'],1);self.assertEqual(len(group['exclusions']),1)
        self.assertIsNone(group['accuracy_ci95']);self.assertIsNone(group['conservative_cluster_bound']['ci95']);self.assertEqual(group['bootstrap']['redraws'],0)
    def test_single_cluster_bootstrap_unavailable(self):
        rows=[r for r in self.fixture() if r['participant_id'].endswith('-1')];r=analyze([self.write(rows)],self.root/'a',count=10)
        self.assertEqual(r['groups']['human / reasoning']['accuracy'],1);self.assertIsNone(r['groups']['human / reasoning']['accuracy_ci95'])
    def test_item_weighting_and_cluster_bound_formula(self):
        rows=[{'item_id':'a','included':True,'correct':True}]*10+[{'item_id':'b','included':True,'correct':False}]
        self.assertEqual(macro(rows,{'a','b'},'correct'),.5)
        rows=[dict(item_id='a',included=True,correct=bool(i%2),form_id='f',form_item_ids=['a'],participant_id=str(i)) for i in range(10)]
        result=cluster_bound(rows,{'a'});self.assertAlmostEqual(result['radius'],math.sqrt(math.log(40)/20));self.assertAlmostEqual(result['weight_sum'],1.)
    def test_confirmatory_gate_and_synthetic_calibration(self):
        with self.assertRaises(AnalysisError):analyze([],self.root/'a',confirmatory=True)
        report=calibrate_bounds(100,17);self.assertIn('SYNTHETIC',report['status']);self.assertEqual(len(report['scenarios']),8)
        self.assertTrue(all(0<=s['empirical_coverage']<=1 for s in report['scenarios']))
    def registered_fixture(self):
        rows=self.fixture();events=[];sessions=set()
        for row in rows:
            row.update(started_at=1767225601.,deadline=1767226081.,finished_at=1767225601.1)
            if row['session_id'] not in sessions:
                sessions.add(row['session_id'])
                event={key:row[key] for key in ('session_id','participant_id','cohort','condition','split','form_id','form_item_ids','agent_metadata','source_provenance','dataset_sha256','forms_sha256','protocol_version','limits')}
                events.append({**event,'record_type':'session','schema_version':'trace.session.v2','created_at':1767225600.})
            events.append({'record_type':'item_started','session_id':row['session_id'],'item_id':row['item_id'],'started_at':row['started_at'],'deadline':row['deadline']})
        # This deliberately synthetic attestation is a unit-test fixture, never study evidence.
        agent=next(row for row in rows if row['cohort']=='agent')
        plan={'schema_version':'trace.analysis-registration.v1','status':'registered',
            'registration_id':'fixture-only','registry_url':'https://registry.test/fixture',
            'registered_at':'2025-12-01T00:00:00Z','reviewed_by':'Synthetic unit-test fixture',
            'dataset_sha256':self.manifest['dataset_sha256'],'forms_sha256':self.manifest['forms_sha256'],
            'protocol_version':PROTOCOL_VERSION,'source_sha256':rows[0]['source_provenance']['source_sha256'],
            'analysis_source_sha256':hashlib.sha256((ROOT/'benchmark/analyze.py').read_bytes()).hexdigest(),
            'split':'test','scope':'panel','condition':'reasoning','agent_system':'agent:fixture',
            'agent_config_sha256':configuration(agent['agent_metadata']),
            'primary_measure':'equal_item_accuracy','direction':'agent minus human','method':'cluster_hoeffding','alpha':.05,
            'human_clusters_per_form':2,'agent_run_clusters':2,
            'assumptions':{name:True for name in REGISTRATION_ASSUMPTIONS}}
        return rows+events,plan
    def test_registered_complete_design_is_operational_and_bootstrap_preserves_run(self):
        rows,plan=self.registered_fixture();registration=self.root/'registration.json';registration.write_text(json.dumps(plan))
        report=analyze([self.write(rows)],self.root/'registered',count=20,confirmatory=True,registration=registration)
        self.assertTrue(report['confirmatory_ready']);self.assertEqual(report['primary_uncertainty'],'cluster_hoeffding')
        self.assertEqual(report['groups']['agent:fixture / reasoning']['bootstrap']['whole_run_clusters'],2)
        self.assertEqual(report['bootstrap_role'],'exploratory only');self.assertTrue(report['contrasts'][0]['primary'])
        self.assertIn('operator attestations',report['registration']['attestation_limit'])
    def test_registration_rejects_draft_drift_late_missing_and_excluded(self):
        original,plan=self.registered_fixture();cases=[]
        for field,value in [('status','draft'),('registered_at','2026-02-01T00:00:00Z'),('source_sha256','a'*64),('human_clusters_per_form',3),('agent_config_sha256','a'*64),('analysis_source_sha256','a'*64)]:
            changed=copy.deepcopy(plan);changed[field]=value;cases.append((original,changed))
        changed=copy.deepcopy(plan);changed['assumptions']['independent_clusters']=False;cases.append((original,changed))
        cases.append((original[1:],plan))
        changed=copy.deepcopy(original);changed[0].update(status='technical_error',attempts_used=0,correct=None,guarantee=None,prevention=None,minimality=None,valid_format=False,reason='synthetic outage');cases.append((changed,plan))
        cases.append((original+[{'record_type':'session_withdrawn','session_id':original[0]['session_id']}],plan))
        cases.append(([row for row in original if row['record_type']=='trial'],plan))
        for index,(events,registration) in enumerate(cases):
            path=self.root/'registration.json';path.write_text(json.dumps(registration))
            with self.assertRaises(AnalysisError):analyze([self.write(events)],self.root/('rejected'+str(index)),count=0,confirmatory=True,registration=path)
    def test_registered_custom_budgets_bind_timelines_and_modalities(self):
        rows,plan=self.registered_fixture()
        limits={'attempts':1,'seconds':900,'probes':0}
        plan.update(schema_version='trace.analysis-registration.v2',limits=limits)
        for row in rows:
            if row['record_type'] in ('trial','session'):row['limits']=limits.copy()
            if 'deadline' in row:row['deadline']=row['started_at']+900
        registration=self.root/'registration.json';registration.write_text(json.dumps(plan))
        report=analyze([self.write(rows)],self.root/'custom-budget',count=0,confirmatory=True,registration=registration)
        self.assertTrue(report['confirmatory_ready'])
        self.assertEqual(report['groups']['human / reasoning']['limits'],limits)
        rows[0]['limits']={'attempts':1,'seconds':480,'probes':0}
        with self.assertRaises(AnalysisError):analyze([self.write(rows)],self.root/'mixed-budget',count=0)
    def test_output_cannot_replace_existing_directory(self):
        with self.assertRaises(AnalysisError):analyze([],self.root,count=0)
if __name__=='__main__':unittest.main()
