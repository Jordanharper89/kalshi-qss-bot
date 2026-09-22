from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OAD_003_BUILD_ID = "OAD-003"
OAD_003_REVISION = "OAD_003_CANONICAL_SOURCE_EVENT_ENVELOPE_V1"

@dataclass(frozen=True)
class CanonicalSourceEvent:
    adapter_id: str
    source_id: str
    entity_id: str
    event_type: str
    source_event_ns: int
    oracle_receive_ns: int
    source_sequence: int
    payload_hash: str
    envelope_hash: str

def build_canonical_source_event(adapter_id, source_id, entity_id, event_type,
                                 source_event_ns, oracle_receive_ns, source_sequence, payload):
    if not all((adapter_id, source_id, entity_id, event_type)):
        raise ValueError("complete event identity required")
    if int(source_event_ns) < 0 or int(oracle_receive_ns) < 0 or int(source_sequence) < 0:
        raise ValueError("non-negative timestamps and sequence required")
    if int(oracle_receive_ns) < int(source_event_ns):
        raise ValueError("Oracle receive time cannot precede source event time")

    payload_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

    raw = {
        "adapter_id": adapter_id,
        "source_id": source_id,
        "entity_id": entity_id,
        "event_type": event_type,
        "source_event_ns": int(source_event_ns),
        "oracle_receive_ns": int(oracle_receive_ns),
        "source_sequence": int(source_sequence),
        "payload_hash": payload_hash,
    }
    envelope_hash = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return CanonicalSourceEvent(
        adapter_id, source_id, entity_id, event_type,
        int(source_event_ns), int(oracle_receive_ns), int(source_sequence),
        payload_hash, envelope_hash
    )

def build_oad_003_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_003_BUILD_ID,
        "revision": OAD_003_REVISION,
        "canonical_source_event": True,
        "latency_timestamps": ("source_event_ns","oracle_receive_ns"),
        "execution": False,
    })

def verify_oad_003_canonical_source_event_envelope():
    e = build_canonical_source_event(
        "kalshi_universal","kalshi","KXTEST","trade",100,120,1,{"price":50}
    )
    return len(e.payload_hash)==64 and len(e.envelope_hash)==64 and e.oracle_receive_ns-e.source_event_ns==20
