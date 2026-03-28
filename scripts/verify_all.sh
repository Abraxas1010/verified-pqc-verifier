#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 cli/verifiedpqc_verify.py \
  --package examples/sample_attestation.json \
  --artifact examples/sample_artifact.txt \
  --json

./scripts/verify_negative_cases.sh
