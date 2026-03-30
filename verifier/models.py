from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class AttestationManifest(BaseModel):
    issued_at: str
    artifact_name: str
    artifact_sha256: str
    artifact_size_bytes: int
    artifact_media_type: str
    metadata: dict[str, Any] = {}
    verifier_bundle_id: str
    verifier_program_id: str
    verifier_program_hash: str
    verifier_certificate_merkle_root: str
    verifier_certificate_sha256: str


class SignatureMaterial(BaseModel):
    algorithm: str
    signer_method: str
    signer_public_key_hex: str
    signed_manifest_hex: str
    signer_key_name: str | None = None
    public_key_format: str | None = None


class VerificationMaterial(BaseModel):
    bundle_dir_hint: str
    cab_certificate: dict[str, Any]
    provenance: dict[str, Any]


class AttestationPackage(BaseModel):
    schema_version: Literal["verified-pqc-attestation-v1"]
    package_id: str
    manifest: AttestationManifest
    signature: SignatureMaterial
    verification_material: VerificationMaterial


class VerificationReport(BaseModel):
    accept: bool
    checked_at: str
    failed_checks: list[str]
    bundle_verification: dict[str, Any] | None = None
    issuer_trust_anchor: dict[str, Any] | None = None
    manifest_sha256: str
    signer_public_key_hex: str
