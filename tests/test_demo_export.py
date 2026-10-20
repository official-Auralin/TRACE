"""Public demo publication boundary and content-bound reproducibility."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmark.core import public_item
from benchmark.demo import ASSETS, export_demo
from tests.test_package_runtime import imported_item, write_package


class DemoExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for relative in ASSETS.values():
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('public fixture asset ' + relative)
        # Extra source files must never be copied by a broad glob.
        (self.source / 'demo/private-token.json').write_text('PRIVATE-OPERATOR-TOKEN')
        (self.source / 'web/app.js').write_text('PRIVATE-SERVER-CLIENT')
        self.patch = patch('benchmark.demo.ROOT', self.source)
        self.patch.start()
        self.item = imported_item()
        self.item.update(key={'explanation': [[0]]}, recipe='PRIVATE-RECIPE',
                         certificate='PRIVATE-CERTIFICATE', provenance='/private/operator/source')
        self.dataset = write_package(self.root / 'package', [self.item])

    def tearDown(self):
        self.patch.stop()
        self.temporary.cleanup()

    def read(self, path):
        return json.loads(path.read_text())

    def test_exact_public_payload_and_narrow_asset_allowlist(self):
        output = self.root / 'site'
        catalog = export_demo(output, self.dataset)
        self.assertEqual(catalog['protocol_version'], 'trace.demo.v1')
        self.assertEqual(catalog['dataset_version'], 'trace-mealy-v5')
        entry = catalog['items'][0]
        self.assertEqual(self.read(output / entry['path']), public_item(self.item))
        self.assertEqual(entry['dimensions'], {'states': 17, 'inputs': 4, 'horizon': 20, 'cells': 80})
        self.assertEqual(entry['split'], 'external')
        self.assertFalse(entry['practice'])
        expected = set(ASSETS) | {'.nojekyll', 'catalog.json', 'lessons.json', 'manifest.json', entry['path']}
        self.assertEqual({str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()}, expected)
        all_bytes = b''.join(path.read_bytes() for path in output.rglob('*') if path.is_file())
        self.assertNotIn(b'PRIVATE-', all_bytes)
        self.assertNotIn(b'/private/operator', all_bytes)
        manifest = self.read(output / 'manifest.json')
        self.assertEqual(set(manifest['files_sha256']), expected - {'manifest.json'})
        for name, expected_hash in manifest['files_sha256'].items():
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), expected_hash)
        self.assertEqual(hashlib.sha256((output / entry['path']).read_bytes()).hexdigest(), entry['sha256'])
        lessons = self.read(output / 'lessons.json')
        self.assertEqual(len(lessons), 5)
        self.assertTrue(all(lesson['id'].startswith('demo-') for lesson in lessons))
        self.assertTrue(all(set(lesson) == {'id', 'title', 'caption', 'item'} for lesson in lessons))
        self.assertTrue(all('key' not in lesson['item'] for lesson in lessons))

    def test_repeatable_bytes_and_separate_content_and_build_identity(self):
        a = export_demo(self.root / 'a', self.dataset)
        b = export_demo(self.root / 'b', self.dataset)
        self.assertEqual(a, b)
        for path in (self.root / 'a').rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (self.root / 'b' / path.relative_to(self.root / 'a')).read_bytes())
        (self.source / 'demo/app.js').write_text('changed public presentation')
        c = export_demo(self.root / 'c', self.dataset)
        self.assertEqual(a['package_id'], c['package_id'])
        self.assertNotEqual(a['build_id'], c['build_id'])
        self.assertEqual(a['items'], c['items'])
        changed = copy.deepcopy(self.item)
        changed['id'] = 'new-task-identity'
        write_package(self.dataset, [changed])
        d = export_demo(self.root / 'd', self.dataset)
        self.assertNotEqual(a['package_id'], d['package_id'])

    def test_item_ids_are_data_not_paths_and_input_order_does_not_set_play_order(self):
        first = copy.deepcopy(self.item)
        first['id'] = '../../outside/<script>alert(1)</script>'
        second = copy.deepcopy(self.item)
        second['id'] = '/absolute/task?secret#value'
        write_package(self.dataset, [first, second])
        catalog = export_demo(self.root / 'site', self.dataset)
        for entry in catalog['items']:
            self.assertRegex(entry['path'], r'^items/[0-9a-f]{64}\.json$')
            self.assertTrue((self.root / 'site' / entry['path']).is_file())
        other = write_package(self.root / 'reordered', [second, first])
        reordered = export_demo(self.root / 'other-site', other)
        self.assertEqual(catalog['items'], reordered['items'])
        self.assertFalse((self.root / 'outside').exists())

    def test_refuses_existing_outputs_private_source_locations_and_symlinks(self):
        existing = self.root / 'existing'
        existing.mkdir()
        precious = existing / 'keep.txt'
        precious.write_text('keep this')
        for target in (existing, self.dataset / 'site', self.source / 'web/site', self.source / 'archive/site'):
            with self.assertRaises(ValueError):
                export_demo(target, self.dataset)
        self.assertEqual(precious.read_text(), 'keep this')
        linked = self.root / 'linked'
        linked.symlink_to(existing, target_is_directory=True)
        with self.assertRaises(ValueError):
            export_demo(linked, self.dataset)
        asset = self.source / 'demo/app.js'
        asset.unlink()
        asset.symlink_to(precious)
        with self.assertRaisesRegex(ValueError, 'unsafe allowlisted'):
            export_demo(self.root / 'unsafe-assets', self.dataset)
        self.assertFalse((self.root / 'unsafe-assets').exists())

    def test_corrupt_board_fails_without_publishing_partial_artifact(self):
        invalid = copy.deepcopy(self.item)
        invalid['board']['layers'][0][0]['one']['value'] = 0
        write_package(self.dataset, [invalid])
        with self.assertRaisesRegex(ValueError, 'counterfactual'):
            export_demo(self.root / 'invalid', self.dataset)
        self.assertFalse((self.root / 'invalid').exists())


if __name__ == '__main__':
    unittest.main()
