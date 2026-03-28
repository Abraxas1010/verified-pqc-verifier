#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT}/dist/release"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

"${ROOT}/scripts/build_release_artifacts.sh"

python3 -m venv "${TMP_DIR}/venv"
source "${TMP_DIR}/venv/bin/activate"
python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install "${DIST_DIR}"/verified_pqc_verifier-*.whl >/dev/null

mkdir -p "${TMP_DIR}/bundle"
tar -C "${TMP_DIR}/bundle" -xzf "${DIST_DIR}"/verified-pqc-verifier-*-bundle.tar.gz
BUNDLE_ROOT="${TMP_DIR}/bundle"

verifiedpqc-verify \
  --asset-root "${BUNDLE_ROOT}" \
  --package "${BUNDLE_ROOT}/examples/sample_attestation.json" \
  --artifact "${BUNDLE_ROOT}/examples/sample_artifact.txt" \
  --json

verifiedpqc-verify --print-compatibility >/dev/null

echo "[release-smoke] installed wheel + bundle tarball verified successfully"
