"""Exact JavaScript demo/Python correspondence and local progress invariants.

The small truth functions and temporal machines are exhaustive over the stated
windows; corpus candidates are sampled plus the canonical solver answer. This
is executable evidence for the JS adapter, not a new kernel proof.
"""
import copy
import itertools
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from benchmark.core import grade, SEMANTICS
from benchmark.game import solve
from benchmark.teaching import practice_feedback

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')


def candidate(item, answer, feedback=False):
    record = {'answer':answer, 'expected':grade(item,answer)}
    if feedback:
        record['tests'] = practice_feedback(item,answer)['tests']
    return record


def run_batch(fixtures=(), invalid_items=()):
    result = subprocess.run([NODE,str(ROOT/'tests/demo_engine_checks.mjs')],
        input=json.dumps({'fixtures':list(fixtures),'invalid_items':list(invalid_items)}),
        text=True,capture_output=True,check=True,cwd=ROOT)
    return json.loads(result.stdout)['checks']


@unittest.skipUnless(NODE, 'Node.js is required for the deployed demo adapter checks')
class DemoEngineTests(unittest.TestCase):
    def test_all_small_boolean_functions_actuals_and_candidates(self):
        fixtures=[]
        for m in (1,2,3):
            for function in range(1 << (1 << m)):
                machine={'inputs':[chr(65+i) for i in range(m)],'states':1,'initial':0,
                    'transitions':[[{'next':0,'output':(function >> v)&1} for v in range(1 << m)]]}
                for actual in range(1 << m):
                    if not (function >> actual)&1:continue
                    item={'id':f'bool-{m}-{function}-{actual}','machine':machine,
                        'observed':[[(actual >> r)&1 for r in range(m)]],'target_step':0}
                    answers=[{'cells':[c for c in range(m) if mask >> c & 1]} for mask in range(1 << m)]
                    answers.append({'verdict':'no_explanation'})
                    fixtures.append({'item':item,'candidates':[candidate(item,a) for a in answers], 'solution':solve(item)})
        self.assertGreater(run_batch(fixtures),10000)

    def test_all_two_state_one_bit_two_step_machines(self):
        fixtures=[]
        for edges in itertools.product(range(4),repeat=4):
            transitions=[[{'next':edges[q*2+v]//2,'output':edges[q*2+v]%2} for v in range(2)] for q in range(2)]
            machine={'inputs':['A'],'states':2,'initial':0,'transitions':transitions}
            for actual in itertools.product((0,1),repeat=2):
                state=transitions[0][actual[0]]['next']
                if not transitions[state][actual[1]]['output']:continue
                item={'id':str(edges)+str(actual),'machine':machine,'observed':[[x] for x in actual],'target_step':1}
                fixtures.append({'item':item,'candidates':[candidate(item,{'cells':[c for c in range(2) if mask >> c & 1]},feedback=True) for mask in range(4)],'solution':solve(item)})
        self.assertEqual(run_batch(fixtures),2560)

    def test_corpus_sampled_candidates_and_every_canonical_solution(self):
        fixtures=[]; rng=random.Random(20261020)
        with (ROOT/'data/items.jsonl').open() as stream:
            for line in stream:
                raw=json.loads(line)
                item={k:raw[k] for k in ('id','machine','observed','target_step')}
                n=len(item['machine']['inputs'])*(item['target_step']+1)
                solution=solve(item)
                answers=[{'cells':[]},{'cells':list(range(n))},{'cells':solution}] if solution is not None else [{'verdict':'no_explanation'}]
                answers += [{'cells':[c for c in range(n) if rng.randrange(2)]} for _ in range(3)]
                fixtures.append({'item':item,'candidates':[candidate(item,a,feedback=i==1) for i,a in enumerate(answers)],'solution':solution})
        self.assertEqual(len(fixtures),1328)
        self.assertGreater(run_batch(fixtures),9000)

    def test_large_window_malformed_answers_and_invalid_instances(self):
        item={'id':'forty-cells','machine':{'inputs':['A'],'states':1,'initial':0,
            'transitions':[[{'next':0,'output':0},{'next':0,'output':1}]]},'observed':[[1] for _ in range(40)],'target_step':39}
        answers=[{'cells':[39]},{'cells':[0]},{'cells':list(range(40))},{'verdict':'no_explanation'},
            None,[],{}, {'cells':[True]},{'cells':[40]},{'cells':[39,39]},{'cells':[1.5]},{'cells':[39],'extra':1}, {'verdict':'no_explanation','cells':[]}]
        invalid=[]
        for key,value in [('target_step',True),('observed',[[1]]),('semantics',{'version':'incorrect'})]:
            altered=copy.deepcopy(item);altered[key]=value;invalid.append(altered)
        altered=copy.deepcopy(item);altered['semantics']={**SEMANTICS,'prevention':'flip every selected value'};invalid.append(altered)
        false=copy.deepcopy(item);false['observed'][-1]=[0];invalid.append(false)
        missing=copy.deepcopy(item);missing['machine']['transitions'][0].pop();invalid.append(missing)
        bad=copy.deepcopy(item);bad['machine']['transitions'][0][0]['next']=1;invalid.append(bad)
        self.assertEqual(run_batch([{'item':item,'candidates':[candidate(item,a,feedback=True) for a in answers],'solution':[39]}],invalid),21)

    def test_agent_transport_preserves_feedback_history_and_first_answer(self):
        item={'id':'a','machine':{'inputs':['A'],'states':1,'initial':0,
            'transitions':[[{'next':0,'output':0},{'next':0,'output':1}]]},'observed':[[1]],'target_step':0}
        catalog={'schema_version':'trace.demo.catalog.v1','protocol_version':'trace.demo.v1',
            'semantics_version':'trace.gp.v2','package_id':'transport-fixture','items':[{'id':'a','band':'small','path':'a.json'}]}
        commands=[{'action':'lesson_reveal','id':'lesson-a'},
            {'action':'lesson','id':'lesson-a','answer':{'cells':[]}},
            {'action':'lesson_reveal','id':'lesson-a'},
            {'action':'lesson','id':'lesson-a','answer':{'cells':[0]}},
            {'action':'lesson_reveal','id':'lesson-a'},
            {'action':'next'},{'action':'reveal'},{'action':'submit','answer':{'cells':[]}},
            {'action':'reveal'},{'action':'retry'},{'action':'submit','answer':{'cells':[0]}},
            {'action':'reveal'},{'action':'next'},{'action':'snapshot'}]
        expected_errors={0,4,6,11} # Neither lesson nor puzzle may reveal before answering or after success.
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name,data in [('catalog.json',catalog),('a.json',item),('lessons.json',[{'id':'lesson-a','item':item,'cases':[{'answer':{'cells':[0]}}]}])]:
                (root/name).write_text(json.dumps(data))
            catalog['items'][0]['sha256']=hashlib.sha256((root/'a.json').read_bytes()).hexdigest()
            catalog['lessons_sha256']=hashlib.sha256((root/'lessons.json').read_bytes()).hexdigest()
            (root/'catalog.json').write_text(json.dumps(catalog))
            output=subprocess.run([NODE,str(ROOT/'demo/agent.mjs'),str(root/'catalog.json')],
                input=''.join(json.dumps(x)+'\n' for x in commands),text=True,capture_output=True,cwd=ROOT,check=True)
        records=[json.loads(line) for line in output.stdout.splitlines()]
        self.assertEqual(len(records),len(commands)+1)
        self.assertEqual(records[0]['status'],'ready')
        for index,record in enumerate(records[1:]):
            self.assertEqual(record['status'],'error' if index in expected_errors else 'ok')
        self.assertEqual(records[-2]['result'],None)
        self.assertEqual(records[-1]['stats']['first_correct'],0)
        self.assertEqual(records[-1]['stats']['completed'],1)
        self.assertEqual(len(records[-1]['history']['entries']['a']['submissions']),2)
        self.assertEqual(records[-1]['history']['entries']['a']['first_submission']['answer'],{'cells':[]})
        self.assertEqual(records[-1]['history']['lessons'][0]['feedback']['correct'],False)
        self.assertNotIn('cases',records[0]['lessons'][0])
        self.assertEqual(records[-1]['history']['lessons'][1]['answer'],{'cells':[0]})
        self.assertTrue(records[-1]['history']['lessons'][2]['assisted'])

    def test_agent_failed_file_integrity_keeps_session_unmodified(self):
        item={'id':'a','machine':{'inputs':['A'],'states':1,'initial':0,
            'transitions':[[{'next':0,'output':0},{'next':0,'output':1}]]},'observed':[[1]],'target_step':0}
        catalog={'schema_version':'trace.demo.catalog.v1','protocol_version':'trace.demo.v1',
            'semantics_version':'trace.gp.v2','package_id':'tamper-fixture','items':[{'id':'a','band':'small','path':'a.json','sha256':'0'*64}],
            'lessons_sha256':hashlib.sha256(b'[]').hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'a.json').write_text(json.dumps(item));(root/'lessons.json').write_bytes(b'[]')
            (root/'catalog.json').write_text(json.dumps(catalog))
            output=subprocess.run([NODE,str(ROOT/'demo/agent.mjs'),str(root/'catalog.json')],
                input='{"action":"next"}\n{"action":"observe"}\n',text=True,capture_output=True,cwd=ROOT,check=True)
            records=[json.loads(line) for line in output.stdout.splitlines()]
            self.assertEqual(records[1]['status'],'error')
            self.assertIn('hash mismatch',records[1]['error'])
            self.assertEqual(records[2]['history']['entries'],{})
            self.assertIsNone(records[2]['current'])
            (root/'lessons.json').write_bytes(b'[{}]')
            failed=subprocess.run([NODE,str(ROOT/'demo/agent.mjs'),str(root/'catalog.json')],
                input='',text=True,capture_output=True,cwd=ROOT)
            self.assertNotEqual(failed.returncode,0)
            self.assertIn('hash mismatch',failed.stderr)

    def test_immutable_first_answer_retries_resume_reveal_and_finite_schedule(self):
        result=subprocess.run([NODE,str(ROOT/'tests/demo_session_checks.mjs')],text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['checks'],60)


if __name__ == '__main__':unittest.main()
