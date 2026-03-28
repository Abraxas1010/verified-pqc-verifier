from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class IssuerTrustAnchor(BaseModel):
    version: str
    issuer_label: str
    signer_method: str
    signer_key_name: str | None = None
    signer_public_key_sha256: str
    notes: str | None = None


def load_issuer_trust_anchor(path: Path) -> IssuerTrustAnchor:
    return IssuerTrustAnchor.model_validate(json.loads(path.read_text()))
