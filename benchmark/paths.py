"""Installed source and default data locations; no construction dependency."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dataset_directory(path=None):
    """Resolve a compiled package directory (or its corpus.json file)."""
    directory = Path(path).expanduser().resolve() if path is not None else ROOT / 'data'
    return directory.parent if directory.name in ('corpus.json','dataset.json','manifest.json') else directory
