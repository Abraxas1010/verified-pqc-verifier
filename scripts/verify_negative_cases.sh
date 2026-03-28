#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - <<'PY' "$ROOT/examples/sample_attestation.json" "$TMP_DIR/tampered_cab.json" "$TMP_DIR/tampered_hint.json"
from pathlib import Path
import json
import sys

src = Path(sys.argv[1])
cab_out = Path(sys.argv[2])
hint_out = Path(sys.argv[3])
data = json.loads(src.read_text())

tampered_cab = json.loads(src.read_text())
tampered_cab["verification_material"]["cab_certificate"]["description"] = "tampered"
cab_out.write_text(json.dumps(tampered_cab, indent=2, sort_keys=True))

tampered_hint = json.loads(src.read_text())
tampered_hint["verification_material"]["bundle_dir_hint"] = "wrong_bundle"
hint_out.write_text(json.dumps(tampered_hint, indent=2, sort_keys=True))
PY

set +e
cab_output="$(python3 cli/verifiedpqc_verify.py --package "$TMP_DIR/tampered_cab.json" --artifact examples/sample_artifact.txt --json 2>&1)"
cab_status=$?
hint_output="$(python3 cli/verifiedpqc_verify.py --package "$TMP_DIR/tampered_hint.json" --artifact examples/sample_artifact.txt --json 2>&1)"
hint_status=$?
set -e

if [[ $cab_status -eq 0 ]]; then
  echo "tampered CAB package unexpectedly accepted" >&2
  exit 1
fi
if [[ $hint_status -eq 0 ]]; then
  echo "tampered bundle hint package unexpectedly accepted" >&2
  exit 1
fi
if [[ "$cab_output" != *"verification_material_cab_certificate"* ]]; then
  echo "expected verification_material_cab_certificate failure not found" >&2
  echo "$cab_output" >&2
  exit 1
fi
if [[ "$hint_output" != *"verification_material_bundle_dir_hint"* ]]; then
  echo "expected verification_material_bundle_dir_hint failure not found" >&2
  echo "$hint_output" >&2
  exit 1
fi

echo "$cab_output" >/dev/null
echo "$hint_output" >/dev/null
