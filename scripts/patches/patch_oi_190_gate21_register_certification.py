from pathlib import Path

ROOT = Path.cwd()
MODULE = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_replay_registry_engine.py"

text = MODULE.read_text(encoding="utf-8")

patch = r'''

# ---------------------------------------------------------------------------
# OI-190 GATE 2.1 REGISTER CERTIFICATION CONTRACT
# Adds the canonical OI-189 -> OI-190 method expected by integration tests:
# register_certification(certification, manifest=None, validation=None)
# ---------------------------------------------------------------------------

class Gate21ReplayRegistrationRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


def _oi190_gate21_safe_dict(value):
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, dict):
            return converted
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _oi190_gate21_hash(value):
    import json
    from hashlib import sha256
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _oi190_gate21_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _oi190_gate21_register_certification(self, certification, manifest=None, validation=None, registry_context=None):
    cert = _oi190_gate21_safe_dict(certification)
    man = _oi190_gate21_safe_dict(manifest)
    val = _oi190_gate21_safe_dict(validation)
    ctx = _oi190_gate21_safe_dict(registry_context)

    if not hasattr(self, "_gate21_records"):
        self._gate21_records = []

    certification_id = str(cert.get("certification_id") or "")
    validation_id = str(cert.get("validation_id") or val.get("validation_id") or "")
    manifest_id = str(
        man.get("manifest_id")
        or cert.get("manifest_id")
        or val.get("target_manifest_id")
        or val.get("manifest_id")
        or ""
    )

    certification_hash = str(cert.get("certification_hash") or "")
    manifest_hash = str(
        man.get("manifest_hash")
        or cert.get("manifest_hash")
        or val.get("target_manifest_hash")
        or val.get("manifest_hash")
        or ""
    )
    chain_hash = str(
        man.get("chain_hash")
        or cert.get("chain_hash")
        or val.get("target_chain_hash")
        or val.get("chain_hash")
        or ""
    )

    certified = bool(cert.get("certified") is True)
    status = "registered" if certified else "rejected"

    payload = {
        "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
        "certification_id": certification_id,
        "validation_id": validation_id,
        "manifest_id": manifest_id,
        "certification_hash": certification_hash,
        "manifest_hash": manifest_hash,
        "chain_hash": chain_hash,
        "certified": certified,
        "status": status,
        "context": ctx,
    }

    registry_hash = _oi190_gate21_hash(payload)

    record = Gate21ReplayRegistrationRecord(
        registration_id="oi190.registration." + registry_hash[:24],
        registry_id="oi190.registry." + registry_hash[:24],
        created_at=_oi190_gate21_now(),
        oracle_instance_id=getattr(self, "oracle_instance_id", "oracle.default"),
        module_id=getattr(self, "module_id", "OI-190"),
        module_name=getattr(self, "module_name", "Oracle Universal Market Adapter Replay Registry Engine"),
        certification_id=certification_id,
        validation_id=validation_id,
        manifest_id=manifest_id,
        certification_hash=certification_hash,
        manifest_hash=manifest_hash,
        chain_hash=chain_hash,
        certified=certified,
        passed=certified,
        status=status,
        registry_hash=registry_hash,
        read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        telemetry={
            "module_id": getattr(self, "module_id", "OI-190"),
            "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
            "certification_id": certification_id,
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "certified": certified,
            "status": status,
        },
        explainability={
            "purpose": "Register certified replay artifacts for institutional lookup.",
            "read_only_reason": "Registry records metadata only and cannot execute, route, submit, or manage positions.",
            "execution_boundary": "Q Series remains the only execution engine.",
        },
    )

    self._gate21_records.append(record)
    return record


def _oi190_gate21_records(self):
    if hasattr(self, "_gate21_records"):
        return list(self._gate21_records)
    return []


UniversalMarketAdapterReplayRegistryEngine.register_certification = _oi190_gate21_register_certification
UniversalMarketAdapterReplayRegistryEngine.records = _oi190_gate21_records
'''

if "OI-190 GATE 2.1 REGISTER CERTIFICATION CONTRACT" not in text:
    text += patch
    MODULE.write_text(text, encoding="utf-8")
    print("[OK] OI-190 Gate 2.1 register_certification contract installed")
else:
    print("[OK] OI-190 Gate 2.1 register_certification contract already installed")

print("Run:")
print("py run_oracle_gate2_1_full_replay_registry_test.py")