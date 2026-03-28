from __future__ import annotations

VERIFIER_VERSION = "0.2.0"
ATTESTATION_SCHEMA_VERSION = "verified-pqc-attestation-v1"
ISSUER_TRUST_ANCHOR_VERSION = "verified-pqc-issuer-trust-anchor-v1"
SUPPORTED_SIGNER_METHODS = ["seeded-ml-dsa", "gcp-kms-ml-dsa-65"]


def compatibility_contract() -> dict[str, object]:
    return {
        "verifier_version": VERIFIER_VERSION,
        "supported_attestation_schema_versions": [ATTESTATION_SCHEMA_VERSION],
        "issuer_trust_anchor_version": ISSUER_TRUST_ANCHOR_VERSION,
        "supported_signer_methods": SUPPORTED_SIGNER_METHODS,
        "bundle_layout_version": "verified-pqc-verifier-bundle-v1",
        "accept_means": [
            "artifact digest matches the manifest",
            "attestation package structure is valid",
            "ML-DSA signature verifies",
            "issuer signing key matches the shipped trust anchor",
            "verifier bundle identity checks pass",
            "CAB certificate and provenance checks pass",
            "embedded package CAB/provenance material matches the pinned local verifier bundle",
        ],
        "accept_does_not_mean": [
            "malware-free",
            "bug-free",
            "semantically correct software",
            "proof of application-level security properties",
        ],
    }
