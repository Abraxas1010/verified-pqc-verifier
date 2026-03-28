<img src="assets/Apoth3osis.webp" alt="Apoth3osis — formal mathematics and verified software" width="140"/>

<sub><strong>Our tech stack is ontological:</strong><br>
<strong>Hardware — Physics</strong><br>
<strong>Software — Mathematics</strong><br><br>
<strong>Our engineering workflow is simple:</strong> discover, build, grow, learn & teach</sub>

---

<sub>
<strong>Acknowledgment</strong><br>
We humbly thank the collective intelligence of humanity for providing the technology and culture we cherish. We do our best to properly reference the authors of the works utilized herein, though we may occasionally fall short. Our formalization acts as a reciprocal validation—confirming the structural integrity of their original insights while securing the foundation upon which we build. In truth, all creative work is derivative; we stand on the shoulders of those who came before, and our contributions are simply the next link in an unbroken chain of human ingenuity.
</sub>

---

[![License: Apoth3osis License Stack v1](https://img.shields.io/badge/License-Apoth3osis%20License%20Stack%20v1-blue.svg)](LICENSE.md)

# VerifiedPQC Verifier

VerifiedPQC Verifier is a standalone offline verifier for VerifiedPQC attestation packages. It verifies artifact digests, ML-DSA signatures, CAB certificate integrity, and verifier-bundle identity without calling the issuing API.

## What Is This?

This repo is the public verification surface for VerifiedPQC attestation packages: a small, auditable verifier library and CLI that recipients can run independently.

## Scope

- offline verification of `verified-pqc-attestation-v1` packages
- ML-DSA-65 signature verification using the vendored PQClean verifier path
- shipped CAB/provenance verification for the acceptance bundle
- optional signer-key pinning by SHA-256

## Quick Start

Install locally:

```bash
python3 -m pip install -e .
```

Run the sample verification:

```bash
./scripts/verify_all.sh
```

Run the CLI directly:

```bash
python3 cli/verifiedpqc_verify.py \
  --package examples/sample_attestation.json \
  --artifact examples/sample_artifact.txt \
  --json
```

## How To Verify

The shipped verifier bundle lives under `public_material/verified_pqc_export_bundle/`.

The verifier checks:

- artifact digest against the manifest
- ML-DSA signature validity
- CAB certificate integrity
- verifier bundle identity fields
- embedded package CAB/provenance material against the pinned local bundle

You can optionally pin an expected signer key:

```bash
python3 cli/verifiedpqc_verify.py \
  --package examples/sample_attestation.json \
  --artifact examples/sample_artifact.txt \
  --expect-signer-key-sha256 <hex>
```

See:

- [verification_contract.md](docs/verification_contract.md)
- [build.md](docs/build.md)

## Repo Layout

- `verifier/`: verification library
- `cli/`: command-line entrypoint
- `scripts/`: build and one-command verification helpers
- `public_material/`: shipped verifier bundle and CAB material
- `examples/`: sample artifact and attestation package
- `vendor/pqc_lattice/`: minimal ML-DSA verifier backend sources

## Accept / Reject

`accept` means the package verified under the local verifier rules.

`accept` does not mean the underlying software is safe, bug-free, or semantically proven.

## License

[Apoth3osis License Stack v1](LICENSE.md)
