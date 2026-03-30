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

Independently verify post-quantum cryptographic attestation packages — offline, without calling the issuing API.

When someone gives you a file and an attestation package, this tool answers one question: **was this exact file signed by a trusted issuer, and has anything been tampered with since?**

## What This Tool Checks

1. **Artifact integrity** — SHA-256 of the file you have matches what the signer attested
2. **Signature validity** — ML-DSA-65 (FIPS 204 / Dilithium3) signature is cryptographically correct
3. **Issuer identity** — the signer's public key matches the shipped trust anchor
4. **Certificate integrity** — CAB certificate Merkle tree is intact
5. **Bundle identity** — embedded verification material matches the pinned local bundle

If all checks pass: `accept = true`. If any check fails: `accept = false` with a list of exactly which checks failed.

## Prerequisites

- Python 3.11+
- A C compiler (gcc or clang)
- OpenSSL development headers (`libssl-dev` on Debian/Ubuntu, `openssl-devel` on RHEL)

## Step-by-Step Verification Guide

### Step 1: Clone this repo

```bash
git clone https://github.com/Abraxas1010/verified-pqc-verifier.git
cd verified-pqc-verifier
```

### Step 2: Install Python dependencies

```bash
python3 -m pip install -e .
```

### Step 3: Build the ML-DSA verification binary

This compiles the PQClean ML-DSA-65 reference implementation into a standalone verification binary. It only needs to be done once.

```bash
bash scripts/build_dsa_open_cli.sh
```

This creates `vendor/pqc_lattice/out/dsa_open_cli_3`. If the build fails, make sure you have `libssl-dev` and a C compiler installed.

### Step 4: Verify an attestation package

You need two files:
- The **attestation package** (a JSON file you received from the attestation issuer)
- The **artifact** (the actual file that was attested — a binary, archive, document, etc.)

```bash
python3 cli/verifiedpqc_verify.py \
  --package /path/to/attestation_package.json \
  --artifact /path/to/the_file_that_was_attested \
  --json
```

**Example using the included sample:**

```bash
python3 cli/verifiedpqc_verify.py \
  --package examples/sample_attestation.json \
  --artifact examples/sample_artifact.txt \
  --json
```

### Step 5: Read the result

**If verification passes:**

```json
{
  "accept": true,
  "failed_checks": [],
  "manifest_sha256": "...",
  "signer_public_key_hex": "..."
}
```

`accept: true` means: the file matches what was signed, the signature is valid, and the signer is the trusted issuer.

**If verification fails:**

```json
{
  "accept": false,
  "failed_checks": ["artifact_sha256", "signature"],
  "manifest_sha256": "...",
  "signer_public_key_hex": "..."
}
```

`failed_checks` tells you exactly what went wrong. Common failures:

| Failed Check | What It Means |
|---|---|
| `artifact_sha256` | The file you have doesn't match what was signed — wrong file, or file was modified |
| `signature` | The ML-DSA signature is invalid — the attestation package was tampered with |
| `issuer_trust_anchor_signer_public_key_sha256` | The signing key doesn't match the trusted issuer — signed by an unknown key |
| `cab_certificate` | The certificate bundle failed integrity checks |
| `schema_version` | The attestation package uses an unsupported format version |

## Text Output Mode

Omit `--json` for a compact text format:

```bash
python3 cli/verifiedpqc_verify.py \
  --package attestation.json \
  --artifact artifact.bin
```

```
accept=True
failed_checks=
manifest_sha256=1271bf8ea5fa8d75284e2584cf6dedde0cfe43b7b0f629a11cc11101ce333cdc
```

The exit code is `0` for accept and `1` for reject, so you can use it in scripts:

```bash
if python3 cli/verifiedpqc_verify.py --package pkg.json --artifact file.bin; then
  echo "Verified"
else
  echo "Verification failed"
fi
```

## Advanced Options

### Pin a specific signing key

If you know the expected SHA-256 of the signer's public key, you can enforce it:

```bash
python3 cli/verifiedpqc_verify.py \
  --package attestation.json \
  --artifact artifact.bin \
  --expect-signer-key-sha256 7582a2a65fb5e75b3c215b8eec75c374ff77d760741d7892d83cb03515cafaec
```

### Installed package mode

After installing via pip, use the `verifiedpqc-verify` command and point to an asset bundle:

```bash
verifiedpqc-verify \
  --asset-root /path/to/verified-pqc-verifier-asset-bundle \
  --package attestation.json \
  --artifact artifact.bin \
  --json
```

### Print compatibility contract

```bash
python3 cli/verifiedpqc_verify.py --print-compatibility
```

This outputs the verifier's supported schema versions, signer methods, and bundle layout version.

## Hosted Attestation Service

Attestation packages are created through the hosted service at:

**[www.agentpmt.com/marketplace/quantum-safe-file-attestation](https://www.agentpmt.com/marketplace/quantum-safe-file-attestation)**

The hosted service signs files with ML-DSA-65 via a Google Cloud KMS hardware security module and returns attestation packages. It is available as a REST API for integration into CI/CD pipelines, automated workflows, and custom tooling.

You can also verify attestation packages through the hosted REST API if you prefer not to set up a local environment. Both creation and verification are available as API endpoints.

**This repo is for independent offline verification.** It lets you confirm attestation packages without any API calls, accounts, or trust in our servers. The cryptographic proof speaks for itself.

## What "Accept" Means — and Doesn't Mean

**Accept means:**
- The artifact's SHA-256 matches the signed manifest
- The ML-DSA-65 signature is cryptographically valid
- The signing key matches the trusted issuer
- The CAB certificate and provenance are intact
- The embedded verification material matches the pinned bundle

**Accept does NOT mean:**
- The software is free of bugs or vulnerabilities
- The software is free of malware
- The software does what it claims to do
- The software is suitable for any particular purpose

The attestation proves **what was signed and by whom** — nothing more.

## Attestation Package Structure

An attestation package is a JSON object with this structure:

```
{
  "schema_version": "verified-pqc-attestation-v1",
  "package_id": "<SHA-256 of canonical manifest>",
  "manifest": {
    "issued_at": "<ISO-8601 UTC timestamp>",
    "artifact_name": "<name of the attested file>",
    "artifact_sha256": "<SHA-256 hex digest of the file>",
    "artifact_size_bytes": <file size>,
    "artifact_media_type": "<MIME type>",
    "metadata": { <freeform key-value pairs set by the signer> },
    "verifier_bundle_id": "verified_pqc_export_bundle",
    "verifier_program_id": "verified_pqc_accept_all_checks",
    "verifier_program_hash": "<SHA-256 of kernel.c>",
    "verifier_certificate_merkle_root": "<Merkle root of CAB artifacts>",
    "verifier_certificate_sha256": "<SHA-256 of certificate.json>"
  },
  "signature": {
    "algorithm": "ML-DSA-65",
    "signer_method": "gcp-kms-ml-dsa-65",
    "signer_public_key_hex": "<1952-byte ML-DSA public key in hex>",
    "signed_manifest_hex": "<signed manifest bytes in hex>",
    "signer_key_name": "<redacted KMS key reference>",
    "public_key_format": "NIST_PQC"
  },
  "verification_material": {
    "bundle_dir_hint": "verified_pqc_export_bundle",
    "cab_certificate": { <full CAB certificate object> },
    "provenance": { <full provenance object> }
  }
}
```

The `metadata` field contains whatever the signer chose to include — version numbers, build info, environment tags, or any other context. It is signed into the manifest and cannot be tampered with.

## Repo Layout

- `verifier/` — verification library (models, signature checking, CAB verification, trust anchor loading)
- `cli/` — command-line entrypoint (`verifiedpqc_verify.py`)
- `scripts/` — build helpers and test scripts
- `public_material/` — shipped trust anchor and CAB verification bundle
- `examples/` — sample artifact and a real, verifiable attestation package
- `vendor/pqc_lattice/` — vendored PQClean ML-DSA-65 source for building the verification binary
- `docs/` — verification contract and build instructions

## License

[Apoth3osis License Stack v1](LICENSE.md)
