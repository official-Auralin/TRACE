"""General executable compilation, counterfactual binding and finite scaling."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from benchmark.compile import LeanProcess,compile_item,compile_dataset,formal_identity,normalize
from benchmark.core import assignment,cell_count,digest,grade,public_item,simulate,validate_item
from benchmark.game import bad_query,bad_root,make_certificate,solve,verify_certificate
from benchmark.level import execute
from benchmark.paths import ROOT
from benchmark.reference import direct_item_table,direct_key,table_execute


class GeneralCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        formal_identity()
        cls.source=json.loads((ROOT/'examples/external-loop.jsonl').read_text())
        with LeanProcess('CompileLevel.lean') as compiler:
            cls.item=compile_item(cls.source,compiler)

    def test_every_word_and_every_candidate_of_external_loop(self):
        item=self.item;n=cell_count(item);actual=simulate(item['machine'],item['observed'])
        self.assertEqual(actual['outputs'],[1,0,1])
        for mask in range(1<<n):
            word=assignment(mask,3,3);out=execute(item['board'],word)
            reference=table_execute(item['machine'],word)
            self.assertEqual(out['outputs'],reference['outputs']);self.assertEqual(out['states'],reference['states'])
        accepted=direct_key(direct_item_table(item))['explanation']
        for mask in range(1<<n):
            selected=[c for c in range(n) if (mask>>c)&1]
            self.assertEqual(grade(item,{'cells':selected})['correct'],selected in accepted)

    def test_determinism_and_no_private_inventory(self):
        with LeanProcess('CompileLevel.lean') as compiler:
            again=compile_item(self.source,compiler)
        self.assertEqual(self.item,again)
        self.assertFalse({'key','certificate','recipe'} & self.item.keys())
        self.assertEqual(len(self.item['board']['switches']),9)

    def test_unobserved_transition_and_cell_corruption_rejected(self):
        item=copy.deepcopy(self.item)
        item['machine']['transitions'][0][0]['output']^=1
        with self.assertRaisesRegex(ValueError,'counterfactual'):validate_item(item)
        item=copy.deepcopy(self.item);root=item['board']['layers'][0][0]
        root['cell']=3
        with self.assertRaisesRegex(ValueError,'cell'):validate_item(item)

    def test_rolling_recurrence_matches_certificates(self):
        item=self.item
        for fixed in ([],[0],[0,4,8],list(range(9))):
            self.assertEqual(bad_root(item,fixed),bad_query(item,fixed)[0][item['machine']['initial']])
        self.assertTrue(verify_certificate(item,make_certificate(item)))

    def test_suffix_is_validated_then_target_prefix_preserved(self):
        record=copy.deepcopy(self.source);record.pop('observed_outputs');record['observed'].append([0,0,0])
        self.assertEqual(normalize(record)['observed'],self.source['observed'])
        record['observed'][-1]=[2,0,0]
        with self.assertRaises(ValueError):normalize(record)
        record=copy.deepcopy(self.source);record['constraints']={}
        with self.assertRaisesRegex(ValueError,'silently dropped'):normalize(record)

    def test_old_caps_are_not_mathematical_limits(self):
        # Deliberately redundant states test infrastructure size, not difficulty.
        record={'id':'large-finite-fixture','machine':{'inputs':['A','B','C','D'],'states':33,'initial':0,
            'transitions':[[{'next':(q+1)%33,'output':v&1} for v in range(16)] for q in range(33)]},
            'observed':[[1,0,0,0] for _ in range(40)],'target_step':39}
        with LeanProcess('CompileLevel.lean') as compiler:item=compile_item(record,compiler)
        self.assertEqual(solve(item),[156]);self.assertTrue(grade(item,{'cells':[156]})['correct'])
        cert=make_certificate(item);self.assertTrue(verify_certificate(item,cert))
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'record.jsonl';path.write_text(json.dumps({'item':public_item(item),'certificate':cert})+'\n')
            run=subprocess.run([str(ROOT/'formal/.build/trace-check'),str(path)],capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(run.returncode,0,run.stderr)

    def test_quiet_and_verbose_packages_match_without_stored_certificates(self):
        from benchmark.runtime import load_package
        with tempfile.TemporaryDirectory() as temp:
            first=Path(temp)/'first';second=Path(temp)/'second';certs=Path(temp)/'proofs.jsonl'
            a=compile_dataset(ROOT/'examples/external-loop.jsonl',first)
            b=compile_dataset(ROOT/'examples/external-loop.jsonl',second,certs,verbose=True)
            self.assertEqual(a,b)
            self.assertEqual(sorted(p.name for p in first.iterdir()),['dataset.json','forms.json','items.jsonl','manifest.json'])
            self.assertNotIn('certificate',json.loads((first/'items.jsonl').read_text()))
            self.assertTrue(certs.is_file())
            _,body,manifest,_=load_package(first)
            self.assertTrue(grade(body['items']['external-memory-loop'],{'cells':solve(self.item)})['correct'])
            self.assertEqual(manifest['dataset_sha256'],a['dataset_sha256'])
            with self.assertRaises(ValueError):compile_dataset(ROOT/'examples/external-loop.jsonl',first)

if __name__=='__main__':unittest.main()
