#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PQ="$ROOT/vendor/pqc_lattice/refc/pqclean"
OUT="$ROOT/vendor/pqc_lattice/out"
SRC="$PQ/crypto_sign/ml-dsa-65/clean"

if [[ ! -d "$SRC" ]]; then
  echo "PQClean ML-DSA-65 sources not found at $SRC" >&2
  exit 1
fi

mkdir -p "$OUT"
COMMON_SRCS=$(ls "$PQ/common"/*.c | grep -v -E 'randombytes.c' || true)

cc -O2 -std=c99 -I"$SRC" -I"$PQ/common" -o "$OUT/dsa_open_cli_3" \
  "$OUT/dsa_open_cli_3.c" \
  "$SRC"/*.c \
  $COMMON_SRCS \
  "$OUT/ml_dsa_randombytes_override.c" -lcrypto

echo "[build] dsa_open_cli_3 built at $OUT/dsa_open_cli_3"
