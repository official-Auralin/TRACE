"""Build a curated, deterministic static lab demo from a compiled task package.

This is a public learning/demo artifact, not a participant server or a research
collection service. It exports the same public task projection used by the
study runtime, never the package directory or operator records. The standalone
dataset constructor and the compiler are not invoked by this command.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from .core import DATA_VERSION, SEMANTICS, canonical, digest, public_item
from .paths import ROOT
from .runtime import load_package
from .teaching import demonstrations


DEMO_VERSION = 'trace.demo.v1'
CATALOG_VERSION = 'trace.demo.catalog.v1'
# No recursive directory copying: every browser source must be admitted here.
ASSETS = {
    'index.html': 'demo/index.html',
    'app.js': 'demo/app.js',
    'engine.js': 'demo/engine.js',
    'session.js': 'demo/session.js',
    'style.css': 'demo/style.css',
    'board.js': 'web/board.js',
    'board-base.css': 'web/style.css',
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (canonical(value) + '\n').encode('ascii')


def safe_output(output, dataset):
    """Never overwrite user files or place public output among private inputs."""
    supplied = Path(output).expanduser()
    if supplied.is_symlink() or supplied.exists():
        raise ValueError('Demo output must be a new directory; existing files are never replaced')
    resolved = supplied.resolve()
    repository = ROOT.resolve()
    package = dataset.resolve()
    if resolved == package or package in resolved.parents or resolved in package.parents:
        raise ValueError('Demo output must be separate from its input package')
    if resolved == repository or resolved in repository.parents:
        raise ValueError('Demo output cannot replace the repository or an ancestor')
    if repository in resolved.parents and repository / 'artifacts' not in resolved.parents:
        raise ValueError('In-repository demo outputs belong in artifacts/, never source or research directories')
    return resolved


def structural_dimensions(item):
    inputs = len(item['machine']['inputs'])
    horizon = item['target_step'] + 1
    return {'states': item['machine']['states'], 'inputs': inputs,
            'horizon': horizon, 'cells': inputs * horizon}


def order_key(entry):
    d = entry['dimensions']
    split_order = {'tutorial': 0, 'pilot': 1, 'development': 2, 'test': 3}
    return (d['cells'], d['horizon'], d['inputs'], d['states'],
            split_order.get(entry['split'], 4), entry['split'], entry['id'])


def export_demo(output, dataset=None):
    directory, body, source_manifest, _ = load_package(dataset)
    destination = safe_output(output, directory)
    assets = {}
    for name, relative in ASSETS.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('Missing or unsafe allowlisted demo asset: ' + relative)
        assets[name] = path.read_bytes()
    # Both interfaces initially receive the visible lesson, not the old study
    # demonstration's solved cases. Feedback/reveal is computed after an action.
    lessons = json_bytes([{key: lesson[key] for key in ('id', 'title', 'caption', 'item')}
                          for lesson in demonstrations()])
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Work only in our own temporary directory; a failure leaves existing data intact.
    with tempfile.TemporaryDirectory(prefix='.trace-build-demo-', dir=destination.parent) as temporary:
        package = Path(temporary) / 'site'
        package.mkdir()
        (package / 'items').mkdir()
        hashes = {}

        def write(relative, raw):
            (package / relative).write_bytes(raw)
            hashes[relative] = sha256(raw)

        for name, raw in assets.items():
            write(name, raw)
        write('.nojekyll', b'')
        write('lessons.json', lessons)
        entries = []
        for item_id in body['items']:
            item = body['items'][item_id]  # validates the hash and all source/board transitions
            public = public_item(item)
            raw = json_bytes(public)
            # IDs are opaque data, never path components (including malicious ../ IDs).
            relative = 'items/' + sha256(item_id.encode('utf-8')) + '.json'
            if relative in hashes:
                raise ValueError('Item path collision')
            write(relative, raw)
            dimensions = structural_dimensions(public)
            band = 'q{states}-m{inputs}-h{horizon}'.format(**dimensions)
            entries.append({'id': item_id, 'path': relative, 'sha256': sha256(raw),
                            'task_sha256': digest(public), 'band': band,
                            'dimensions': dimensions, 'split': item['split'],
                            'practice': item['split'] == 'tutorial'})
        entries.sort(key=order_key)
        bands = {}
        for entry in entries:
            band = entry['band']
            if band not in bands:
                d = entry['dimensions']
                bands[band] = {'id': band, 'dimensions': d, 'count': 0,
                               'label': f"{d['states']} routes · {d['inputs']} inputs · {d['horizon']} moments"}
            bands[band]['count'] += 1
        catalog = {
            'schema_version': CATALOG_VERSION, 'protocol_version': DEMO_VERSION,
            'semantics_version': SEMANTICS['version'], 'dataset_version': DATA_VERSION,
            'dataset_sha256': source_manifest['dataset_sha256'],
            'exposure': 'public_demo_all_exported_items',
            'collection': 'none; progress remains in this browser unless explicitly downloaded',
            'difficulty_status': 'structural_bands_not_empirically_calibrated',
            'lessons_path': 'lessons.json', 'lessons_sha256': sha256(lessons),
            'teaching_disclosure': 'lessons contain only visible introductory tasks; feedback and solutions follow explicit actions',
            'assets_sha256': {name: sha256(raw) for name, raw in sorted(assets.items())},
            'n_items': len(entries), 'bands': list(bands.values()), 'items': entries,
        }
        # Learning history binds the tasks, their sequence, teaching and protocol.
        # Cosmetic asset updates retain progress; incompatible behavior must bump
        # the demo protocol. A separate build ID binds every catalog/asset byte.
        catalog['package_id'] = digest({
            'protocol_version': DEMO_VERSION, 'semantics_version': SEMANTICS['version'],
            'dataset_version': DATA_VERSION, 'lessons_sha256': sha256(lessons), 'items': entries})
        catalog['build_id'] = digest(catalog)
        write('catalog.json', json_bytes(catalog))
        manifest = {'schema_version': 'trace.demo.manifest.v1',
                    'protocol_version': DEMO_VERSION, 'package_id': catalog['package_id'],
                    'build_id': catalog['build_id'],
                    'files_sha256': dict(sorted(hashes.items())),
                    'validation_scope': 'Hash-bound compiled input; independent public-item source/board validation. Full certification is a separate mandatory release gate.'}
        (package / 'manifest.json').write_bytes(json_bytes(manifest))
        if destination.exists() or destination.is_symlink():
            raise ValueError('Demo output appeared during export; existing files are never replaced')
        package.rename(destination)
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', help='compiled task package; defaults to data/')
    parser.add_argument('--output', required=True, help='new static artifact directory, e.g. artifacts/pages-demo')
    args = parser.parse_args()
    try:
        catalog = export_demo(args.output, args.dataset)
    except (OSError, ValueError) as error:
        parser.exit(1, json.dumps({'status': 'ERROR', 'error': str(error)}) + '\n')
    print(json.dumps({'status': 'PASS', 'protocol_version': DEMO_VERSION,
                      'items': catalog['n_items'], 'package_id': catalog['package_id'],
                      'output': args.output,
                      'scope': 'Static export and source/board validation; not a research collection service'}))


if __name__ == '__main__':
    main()
