from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cab import verify_certificate
from .models import AttestationPackage, VerificationReport


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_DIR = ROOT / "public_material" / "verified_pqc_export_bundle"
OPEN_CLI = ROOT / "vendor" / "pqc_lattice" / "out" / "dsa_open_cli_3"
BUILD_SCRIPT = ROOT / "scripts" / "build_dsa_open_cli.sh"
SCHEMA_VERSION = "verified-pqc-attestation-v1"
SIGNER_METHODS = {"seeded-ml-dsa", "gcp-kms-ml-dsa-65"}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], *, cwd: Path, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, check=False)


def ensure_dsa_backend() -> None:
    if OPEN_CLI.exists():
        return
    proc = run(["bash", str(BUILD_SCRIPT)], cwd=ROOT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode() or proc.stdout.decode())


def dsa_open_matches(*, pk: bytes, msg: bytes, sm: bytes) -> bool:
    ensure_dsa_backend()
    payload = (
        f"pk = {pk.hex()}\n"
        f"mlen = {len(msg)}\n"
        f"smlen = {len(sm)}\n"
        f"msg = {msg.hex()}\n"
        f"sm = {sm.hex()}\n"
    ).encode()
    proc = run([str(OPEN_CLI)], cwd=ROOT, stdin=payload)
    return proc.returncode == 0


def kernel_program_hash(bundle_dir: Path) -> str:
    return sha256_hex((bundle_dir / "kernel.c").read_bytes())


def bundle_id(bundle_dir: Path) -> str:
    return bundle_dir.name


def verify_attestation_package(
    pkg: AttestationPackage,
    artifact_sha256: str,
    *,
    bundle_dir: Path | None = None,
    expected_signer_key_sha256: str | None = None,
) -> VerificationReport:
    failed: list[str] = []
    bundle = (bundle_dir or DEFAULT_BUNDLE_DIR).resolve()
    cert_path = bundle / "certificate.json"
    prov_path = bundle / "provenance.json"

    if pkg.schema_version != SCHEMA_VERSION:
        failed.append("schema_version")

    manifest_dict = pkg.manifest.model_dump()
    manifest_bytes = canonical_json_bytes(manifest_dict)
    if artifact_sha256.lower() != pkg.manifest.artifact_sha256.lower():
        failed.append("artifact_sha256")

    expected_pkg_id = sha256_hex(manifest_bytes)
    if expected_pkg_id != pkg.package_id:
        failed.append("package_id")
    if pkg.verification_material.bundle_dir_hint != pkg.manifest.verifier_bundle_id:
        failed.append("verification_material_bundle_dir_hint")

    if pkg.signature.algorithm != "ML-DSA-65":
        failed.append("signature_algorithm")
    if pkg.signature.signer_method not in SIGNER_METHODS:
        failed.append("signer_method")
    if pkg.signature.signer_method == "gcp-kms-ml-dsa-65" and pkg.signature.public_key_format not in {None, "NIST_PQC"}:
        failed.append("public_key_format")

    signer_pk = bytes.fromhex(pkg.signature.signer_public_key_hex)
    if expected_signer_key_sha256 is not None:
        if sha256_hex(signer_pk) != expected_signer_key_sha256.lower():
            failed.append("signer_public_key_sha256")

    sig_ok = dsa_open_matches(pk=signer_pk, msg=manifest_bytes, sm=bytes.fromhex(pkg.signature.signed_manifest_hex))
    if not sig_ok:
        failed.append("signature")

    bundle_report: dict[str, Any] | None = None
    if not cert_path.is_file():
        failed.append("bundle_certificate_missing")
    elif not prov_path.is_file():
        failed.append("bundle_provenance_missing")
    else:
        cert = json.loads(cert_path.read_text())
        prov = json.loads(prov_path.read_text())
        bundle_report = verify_certificate(cert_path)
        if not bundle_report["success"]:
            failed.append("cab_certificate")
        if pkg.manifest.verifier_bundle_id != bundle_id(bundle):
            failed.append("verifier_bundle_id")
        if pkg.verification_material.cab_certificate != cert:
            failed.append("verification_material_cab_certificate")
        if pkg.verification_material.provenance != prov:
            failed.append("verification_material_provenance")
        if kernel_program_hash(bundle) != pkg.manifest.verifier_program_hash:
            failed.append("verifier_program_hash")
        if cert.get("merkle_root", "") != pkg.manifest.verifier_certificate_merkle_root:
            failed.append("verifier_certificate_merkle_root")
        if sha256_hex(cert_path.read_bytes()) != pkg.manifest.verifier_certificate_sha256:
            failed.append("verifier_certificate_sha256")
        if prov.get("program_id", "") != pkg.manifest.verifier_program_id:
            failed.append("verifier_program_id")

    return VerificationReport(
        accept=not failed,
        checked_at=now_utc(),
        failed_checks=failed,
        bundle_verification=bundle_report,
        manifest_sha256=sha256_hex(manifest_bytes),
        signer_public_key_hex=pkg.signature.signer_public_key_hex,
    )
