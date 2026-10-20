"""Independent boundaries between a valid imported task and release policies."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from benchmark.compile import LeanProcess, compile_dataset, compile_item, normalize
from benchmark.construct import records
from benchmark.core import assignment, cell_count, grade, public_item, simulate, validate_item
from benchmark.game import make_certificate
from benchmark.paths import ROOT
from benchmark.level import execute, switches
from benchmark.runtime import load_package
from benchmark.validate import validate


class GeneralImportAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        first = json.loads((ROOT / 'examples/external-loop.jsonl').read_text())
        second = copy.deepcopy(first)
        second['id'] = 'same-machine-different-recording'
        second.pop('observed_outputs', None)
        for number in range(1 << cell_count(first)):
            word = assignment(number, 3, 3)
            if word != first['observed'] and simulate(first['machine'], word)['outputs'][-1] == 1:
                second['observed'] = word
                break
        cls.source = cls.root / 'records.jsonl'
        cls.source.write_text('\n'.join(json.dumps(record) for record in (first, second)) + '\n')
        cls.package = cls.root / 'package'
        compile_dataset(cls.source, cls.package)
        single = cls.root / 'single.jsonl'
        single.write_text(json.dumps(first) + '\n')
        cls.single_package = cls.root / 'single-package'
        compile_dataset(single, cls.single_package)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_multiple_recordings_of_one_machine_remain_valid(self):
        _, body, _, _ = load_package(self.package)
        self.assertEqual(len(body['items']), 2)
        report = validate(self.package)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['canonical_certificates_checked'], 2)

    def test_optional_family_metadata_is_validated_before_publication(self):
        source = json.loads((ROOT / 'examples/external-loop.jsonl').read_text())
        source['family'] = {'mistaken': 'object'}
        with self.assertRaises(ValueError):
            normalize(source)

    def test_different_original_cells_have_distinct_display_labels(self):
        controls = switches([[0,0] for _ in range(12)], ['A','A1'])
        self.assertEqual(len({control['label'] for control in controls}), 24)

    def test_modified_visual_metadata_is_rejected(self):
        _, body, _, _ = load_package(self.single_package)
        original = body['items']['external-memory-loop']
        for field, value in (('value', True), ('step', 0.0),
                             ('label', original['board']['switches'][1]['label'])):
            with self.subTest(field=field):
                item = copy.deepcopy(original)
                item['board']['switches'][0][field] = value
                with self.assertRaises(ValueError):
                    validate_item(item)

    def test_constructor_filters_report_impossibility_or_budget_exhaustion(self):
        with self.assertRaises(ValueError):
            list(records(1, 1, 1, 2, 0, temporal=True))
        with self.assertRaises(ValueError):
            list(records(1, 2, 1, 1, 0, temporal=True))
        with self.assertRaises(ValueError):
            list(records(5, 1, 1, 1, 0))
        with self.assertRaises(TimeoutError):
            list(records(2, 2, 1, 2, 0, max_attempts=1))
        # A generic finite import/constructor must still allow memoryless data.
        self.assertEqual(len(list(records(1, 1, 1, 2, 0))), 1)

    def test_import_never_silently_discards_alternate_target_semantics(self):
        source = json.loads((ROOT / 'examples/external-loop.jsonl').read_text())
        for field, value in (('target_output', 0), ('target', {'at':2,'output':0}),
                             ('constraints', {'forbidden_inputs':[[0,0,0]]})):
            with self.subTest(field=field):
                malformed = {**source, field:value}
                with self.assertRaises(ValueError):
                    normalize(malformed)

    def test_certificate_export_preserves_existing_evidence(self):
        path = self.root / 'preserved-evidence.jsonl'
        path.write_text('existing evidence must remain byte-identical\n')
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            validate(self.single_package, emit_certificates=path)
        self.assertEqual(path.read_bytes(), before)

    def test_no_explanation_is_certified_and_not_the_empty_answer(self):
        source = self.root / 'constant.jsonl'
        source.write_text(json.dumps({
            'id':'constant-positive', 'split':'tutorial',
            'machine':{'inputs':['A'], 'states':1, 'initial':0,
                       'transitions':[[{'next':0,'output':1},{'next':0,'output':1}]]},
            'observed':[[0],[1]], 'target_step':1}) + '\n')
        package = self.root / 'constant-package'
        manifest = compile_dataset(source, package)
        self.assertEqual(manifest['certification']['status'], 'PASS')
        _, body, _, _ = load_package(package)
        item = body['items']['constant-positive']
        self.assertEqual(item['board']['layers'][0][0]['kind'], 'output')
        self.assertEqual(len(item['board']['switches']), 2)
        self.assertTrue(grade(item, {'verdict':'no_explanation'})['correct'])
        self.assertFalse(grade(item, {'cells':[]})['correct'])

    def test_nonzero_initial_state_and_earlier_target(self):
        source = json.loads((ROOT / 'examples/external-loop.jsonl').read_text())
        source['machine']['initial'] = 1
        source['observed'] = [[0,0,0],[0,1,0],[1,1,0]]
        source['observed_outputs'] = [1,0,1]
        source['target_step'] = 0
        with LeanProcess('CompileLevel.lean') as compiler:
            item = compile_item(source, compiler)
        self.assertEqual(item['observed'], [[0,0,0]])
        self.assertEqual(item['board']['initial'], 1)
        for number in range(8):
            word = assignment(number, 3, 1)
            actual = execute(item['board'], word)
            expected = simulate(source['machine'], word)
            self.assertEqual(actual['states'], expected['states'])
            self.assertEqual(actual['outputs'], expected['outputs'])

    def test_native_sparse_checker_rejects_adversarial_records(self):
        _, body, _, _ = load_package(self.single_package)
        item = body['items']['external-memory-loop']
        certificate = make_certificate(item)
        variants = []
        bad = copy.deepcopy(certificate)
        bad['queries'].pop()
        variants.append(('missing required query', bad))
        bad = copy.deepcopy(certificate)
        bad['queries'].append(copy.deepcopy(bad['queries'][0]))
        variants.append(('duplicate query', bad))
        bad = copy.deepcopy(certificate)
        bad['queries'][0]['bad_layers'][0][0] ^= True
        variants.append(('forged recurrence', bad))
        bad = copy.deepcopy(certificate)
        bad['queries'][0]['fixed_cells'] = [0]
        variants.append(('changed query binding', bad))
        bad = copy.deepcopy(certificate)
        next(query for query in bad['queries'] if query['failure_inputs'] is not None)['failure_inputs'] = None
        variants.append(('omitted defeating witness', bad))
        bad = copy.deepcopy(certificate)
        bad['actual_execution']['outputs'][-1] = 0
        variants.append(('incorrect actual replay', bad))
        bad = copy.deepcopy(certificate)
        bad['answer'] = {'verdict':'no_explanation'}
        variants.append(('false no-explanation claim', bad))
        for description, forged in variants:
            with self.subTest(description=description):
                run = subprocess.run([str(ROOT / 'formal/.build/trace-check'), '-'],
                    input=json.dumps({'item':public_item(item), 'certificate':forged}) + '\n',
                    text=True, capture_output=True, cwd=ROOT)
                self.assertNotEqual(run.returncode, 0, description)
                self.assertIn('FAIL', run.stderr)

    def test_native_adapters_share_nonempty_input_name_requirement(self):
        source = json.loads((ROOT / 'examples/external-loop.jsonl').read_text())
        source['machine']['inputs'][0] = ''
        _, body, _, _ = load_package(self.single_package)
        item = body['items']['external-memory-loop']
        record = {'item':public_item(item), 'certificate':make_certificate(item)}
        record['item']['machine']['inputs'][0] = ''
        for executable, value in (('trace-compile', source), ('trace-check', record)):
            with self.subTest(executable=executable):
                run = subprocess.run([str(ROOT / 'formal/.build' / executable)],
                    input=json.dumps(value) + '\n', text=True, capture_output=True, cwd=ROOT)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn('empty input name', run.stderr)


if __name__ == '__main__':
    unittest.main()
