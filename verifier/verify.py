from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .cab import verify_certificate
from .models import AttestationPackage, VerificationReport
from .trust_anchor import load_issuer_trust_anchor
from .version import ATTESTATION_SCHEMA_VERSION, SUPPORTED_SIGNER_METHODS


ROOT = Path(__file__).resolve().parents[1]


def verifier_root() -> Path:
    configured = os.environ.get("VERIFIED_PQC_VERIFIER_ROOT", "").strip()
    if configured:
        return Path(configured).resolve()
    return ROOT


def default_bundle_dir() -> Path:
    return verifier_root() / "public_material" / "verified_pqc_export_bundle"


def default_issuer_trust_anchor_path() -> Path:
    return verifier_root() / "public_material" / "issuer_trust_anchor.json"


def open_cli_path() -> Path:
    return verifier_root() / "vendor" / "pqc_lattice" / "out" / "dsa_open_cli_3"


def build_script_path() -> Path:
    return verifier_root() / "scripts" / "build_dsa_open_cli.sh"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], *, cwd: Path, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, check=False)


def ensure_dsa_backend() -> None:
    open_cli = open_cli_path()
    if open_cli.exists():
        return
    build_script = build_script_path()
    if not build_script.is_file():
        raise RuntimeError(
            f"missing ML-DSA verifier build script at {build_script}; set VERIFIED_PQC_VERIFIER_ROOT to a verifier asset bundle"
        )
    proc = run(["bash", str(build_script)], cwd=verifier_root())
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
    proc = run([str(open_cli_path())], cwd=verifier_root(), stdin=payload)
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
    issuer_trust_anchor_path: Path | None = None,
    expected_signer_key_sha256: str | None = None,
) -> VerificationReport:
    failed: list[str] = []
    bundle = (bundle_dir or default_bundle_dir()).resolve()
    trust_anchor_path = (issuer_trust_anchor_path or default_issuer_trust_anchor_path()).resolve()
    cert_path = bundle / "certificate.json"
    prov_path = bundle / "provenance.json"

    if pkg.schema_version != ATTESTATION_SCHEMA_VERSION:
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
    if pkg.signature.signer_method not in SUPPORTED_SIGNER_METHODS:
        failed.append("signer_method")
    if pkg.signature.signer_method == "gcp-kms-ml-dsa-65" and pkg.signature.public_key_format not in {None, "NIST_PQC"}:
        failed.append("public_key_format")

    signer_pk = bytes.fromhex(pkg.signature.signer_public_key_hex)
    trust_anchor_report: dict[str, Any] | None = None
    if not trust_anchor_path.is_file():
        failed.append("issuer_trust_anchor_missing")
    else:
        trust_anchor = load_issuer_trust_anchor(trust_anchor_path)
        trust_anchor_report = trust_anchor.model_dump()
        if trust_anchor.version != "verified-pqc-issuer-trust-anchor-v1":
            failed.append("issuer_trust_anchor_version")
        if trust_anchor.signer_method != pkg.signature.signer_method:
            failed.append("issuer_signer_method")
        if trust_anchor.signer_key_name != pkg.signature.signer_key_name:
            failed.append("issuer_signer_key_name")
        if sha256_hex(signer_pk) != trust_anchor.signer_public_key_sha256.lower():
            failed.append("signer_public_key_sha256")
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
        issuer_trust_anchor=trust_anchor_report,
        manifest_sha256=sha256_hex(manifest_bytes),
        signer_public_key_hex=pkg.signature.signer_public_key_hex,
    )
