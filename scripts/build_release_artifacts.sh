#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT}/dist/release"
VERSION="$(python3 - <<'PY'
from verifier.version import VERIFIER_VERSION
print(VERIFIER_VERSION)
PY
)"

rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"

python3 -m pip wheel "${ROOT}" --no-deps -w "${DIST_DIR}"

git -C "${ROOT}" archive --format=tar.gz --prefix="verified-pqc-verifier-${VERSION}/" HEAD > \
  "${DIST_DIR}/verified-pqc-verifier-${VERSION}-source.tar.gz"

tar -C "${ROOT}" -czf "${DIST_DIR}/verified-pqc-verifier-${VERSION}-bundle.tar.gz" \
  README.md LICENSE.md docs examples public_material vendor scripts/build_dsa_open_cli.sh scripts/verify_all.sh scripts/verify_negative_cases.sh

python3 - <<'PY' "${DIST_DIR}" "${VERSION}"
import hashlib
import json
import sys
from pathlib import Path

from verifier.version import compatibility_contract

dist = Path(sys.argv[1])
version = sys.argv[2]
compat_path = dist / f"verified-pqc-verifier-{version}-compatibility.json"
compat_path.write_text(json.dumps(compatibility_contract(), indent=2, sort_keys=True) + "\n")

manifest = {"version": version, "artifacts": []}
for path in sorted(dist.iterdir()):
    if path.is_file():
        manifest["artifacts"].append(
            {
                "name": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
(dist / f"verified-pqc-verifier-{version}-release-manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n"
)
PY

echo "[release] artifacts written to ${DIST_DIR}"
