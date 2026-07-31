"""
SHA-256 Cryptographic Hashing Utilities for Phase 4 Events & Exports
"""
import hashlib
import json
from typing import Dict, Any, Optional

def compute_sha256_hash(data: str) -> str:
    """Returns hexadecimal SHA-256 digest of input string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def compute_canonical_event_hash(payload_data: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
    """Computes SHA-256 hash over canonical event payload for tamper-proof verification."""
    canonical_bytes = json.dumps(payload_data, sort_keys=True).encode("utf-8")
    hasher = hashlib.sha256(canonical_bytes)
    if previous_hash:
        hasher.update(previous_hash.encode("utf-8"))
    return hasher.hexdigest()
