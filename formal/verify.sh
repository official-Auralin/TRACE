#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_dir="$(dirname -- "$script_dir")"
cd -- "$repository_dir"
PYTHONDONTWRITEBYTECODE=1 python3 -B "$script_dir/build.py" "$@"
