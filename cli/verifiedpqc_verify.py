from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verifier.models import AttestationPackage
from verifier.verify import sha256_hex, verify_attestation_package


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, help="path to attestation package json")
    parser.add_argument("--artifact", required=True, help="path to the artifact being verified")
    parser.add_argument("--bundle-dir", help="optional path to shipped verifier bundle")
    parser.add_argument("--expect-signer-key-sha256", help="optional expected SHA-256 of the raw signer public key")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    pkg = AttestationPackage.model_validate(json.loads(Path(args.package).read_text()))
    artifact_sha = sha256_hex(Path(args.artifact).read_bytes())
    bundle_dir = Path(args.bundle_dir).resolve() if args.bundle_dir else None
    report = verify_attestation_package(
        pkg,
        artifact_sha256=artifact_sha,
        bundle_dir=bundle_dir,
        expected_signer_key_sha256=args.expect_signer_key_sha256,
    )
    if args.json:
        print(json.dumps(report.model_dump(), indent=2, sort_keys=True))
    else:
        print(f"accept={report.accept}")
        print(f"failed_checks={','.join(report.failed_checks)}")
        print(f"manifest_sha256={report.manifest_sha256}")
    return 0 if report.accept else 1


if __name__ == "__main__":
    raise SystemExit(main())
