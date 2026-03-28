# Verification Contract

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
