from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hex_encode(data: bytes) -> str:
    return "0x" + data.hex()


def tagged_hash(tag: str, payload: bytes) -> bytes:
    return sha256(tag.encode("utf-8") + payload)


def cat_sorted(a: bytes, b: bytes) -> bytes:
    return a + b if a <= b else b + a


def merkle_parent(a: bytes, b: bytes) -> bytes:
    return tagged_hash("LoF.Merkle.Node|", cat_sorted(a, b))


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return sha256(b"")
    if len(leaves) == 1:
        return leaves[0]
    xs = leaves[:]
    while len(xs) > 1:
        nxt: list[bytes] = []
        i = 0
        while i < len(xs):
            if i + 1 < len(xs):
                nxt.append(merkle_parent(xs[i], xs[i + 1]))
            else:
                nxt.append(xs[i])
            i += 2
        xs = nxt
    return xs[0]


def verify_certificate(cert_path: Path) -> dict[str, object]:
    cert = json.loads(cert_path.read_text())
    base_dir = cert_path.parent
    artifacts = cert.get("artifacts", [])
    expected_root = cert.get("merkle_root", "")

    failed: list[str] = []
    leaves: list[bytes] = []
    for artifact in artifacts:
        rel_name = artifact.get("name", "")
        expected_hash = artifact.get("sha256", "")
        artifact_path = (base_dir / rel_name).resolve()
        # Guard against path traversal via malicious artifact names (e.g. "../../etc/passwd")
        if not artifact_path.is_relative_to(base_dir.resolve()):
            failed.append(f"{rel_name} (path traversal blocked)")
            continue
        if not artifact_path.is_file():
            failed.append(f"{rel_name} (not found)")
            continue
        digest = sha256(artifact_path.read_bytes())
        observed_hash = hex_encode(digest)
        if observed_hash != expected_hash:
            failed.append(rel_name)
            continue
        leaves.append(digest)

    computed_root = hex_encode(merkle_root(leaves)) if leaves else ""
    if not failed and computed_root != expected_root:
        failed.append("merkle_root")

    return {
        "success": not failed,
        "merkle_root": computed_root,
        "artifact_count": len(artifacts),
        "failed_artifacts": failed,
    }
