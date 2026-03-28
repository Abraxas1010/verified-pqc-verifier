# Verification Contract

Current verifier compatibility contract:

- verifier version: `0.2.0`
- supported attestation schema: `verified-pqc-attestation-v1`
- supported signer methods:
  - `seeded-ml-dsa`
  - `gcp-kms-ml-dsa-65`
- bundle layout version: `verified-pqc-verifier-bundle-v1`

`accept` means:

- the artifact digest matches the manifest
- the package structure is valid
- the ML-DSA signature verifies
- the shipped verifier bundle identity checks pass
- the CAB certificate and provenance checks pass
- the package's embedded CAB/provenance material matches the pinned local verifier bundle

`accept` does not mean:

- malware-free
- bug-free
- semantically correct software
- proof of application-level security properties

The CLI emits the same contract as JSON via:

```bash
python3 cli/verifiedpqc_verify.py --print-compatibility
```
