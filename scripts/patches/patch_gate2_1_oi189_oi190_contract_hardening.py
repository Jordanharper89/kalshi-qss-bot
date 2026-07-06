from pathlib import Path

ROOT = Path.cwd()

OI189 = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_query_replay_certification_engine.py"
OI190 = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_replay_registry_engine.py"

# -----------------------------
# Patch OI-189 warning handling
# -----------------------------
text189 = OI189.read_text(encoding="utf-8")

target = '''    blocker_count = sum(1 for f in findings if f.severity in {"critical", "error"})
    warning_count = sum(1 for f in findings if f.severity in {"warning", "info"})
'''

replacement = '''    source_warning_count = int(
        data.get("warning_count")
        or _oi189_contract_safe_dict(data.get("telemetry")).get("warning_count")
        or 0
    )
    source_info_count = int(
        data.get("info_count")
        or _oi189_contract_safe_dict(data.get("telemetry")).get("info_count")
        or 0
    )

    if source_warning_count > 0:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_WARNINGS_PRESENT",
            severity="warning",
            message="Validation completed with non-blocking warnings.",
            evidence={"warning_count": source_warning_count},
        ))

    if source_info_count > 0 and not any(f.code == "VALIDATION_FINDINGS_PRESENT" for f in findings):
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_INFO_PRESENT",
            severity="info",
            message="Validation completed with non-blocking informational findings.",
            evidence={"info_count": source_info_count},
        ))

    blocker_count = sum(1 for f in findings if f.severity in {"critical", "error"})
    warning_count = sum(1 for f in findings if f.severity in {"warning", "info"})
'''

if target in text189:
    text189 = text189.replace(target, replacement)
    OI189.write_text(text189, encoding="utf-8")
    print("[OK] OI-189 warning contract patched")
else:
    print("[OK] OI-189 warning contract target not found; leaving as-is")

# -----------------------------
# Patch OI-190 registry adapter
# -----------------------------
text190 = OI190.read_text(encoding="utf-8")

append190 = r'''

# ---------------------------------------------------------------------------
# OI-190 GATE 2.1 CONTRACT ADAPTER
# Adds register_certification() and records() compatibility for the replay
# certification handoff used by OI-189 -> OI-190 -> OI-191 integration tests.
# ---------------------------------------------------------------------------

class _OI190ContractRegistration:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


def _oi190_contract_safe_dict(value):
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


def _oi190_contract_hash(value):
    import json
    from hashlib import sha256
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _oi190_contract_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _oi190_register_certification(self, certification, manifest=None, validation=None, registry_context=None):
    cert = _oi190_contract_safe_dict(certification)
    man = _oi190_contract_safe_dict(manifest)
    val = _oi190_contract_safe_dict(validation)
    ctx = _oi190_contract_safe_dict(registry_context)

    if not hasattr(self, "_records"):
        self._records = []

    certification_id = str(cert.get("certification_id") or "")
    manifest_id = str(
        man.get("manifest_id")
        or cert.get("manifest_id")
        or val.get("target_manifest_id")
        or val.get("manifest_id")
        or ""
    )
    validation_id = str(cert.get("validation_id") or val.get("validation_id") or "")
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

    passed = bool(cert.get("certified") is True or cert.get("certification_level") in {"certified", "certified_with_warnings"})

    payload = {
        "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
        "certification_id": certification_id,
        "validation_id": validation_id,
        "manifest_id": manifest_id,
        "certification_hash": certification_hash,
        "manifest_hash": manifest_hash,
        "chain_hash": chain_hash,
        "passed": passed,
        "context": ctx,
    }
    registry_hash = _oi190_contract_hash(payload)

    registration = _OI190ContractRegistration(
        registration_id="oi190.registration." + registry_hash[:24],
        registry_id="oi190.registry." + registry_hash[:24],
        created_at=_oi190_contract_now(),
        oracle_instance_id=getattr(self, "oracle_instance_id", "oracle.default"),
        module_id=getattr(self, "module_id", "OI-190"),
        module_name=getattr(self, "module_name", "Oracle Universal Market Adapter Replay Registry Engine"),
        certification_id=certification_id,
        validation_id=validation_id,
        manifest_id=manifest_id,
        certification_hash=certification_hash,
        manifest_hash=manifest_hash,
        chain_hash=chain_hash,
        passed=passed,
        certified=passed,
        status="registered" if passed else "rejected",
        registry_hash=registry_hash,
        read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        telemetry={
            "module_id": getattr(self, "module_id", "OI-190"),
            "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
            "certification_id": certification_id,
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "passed": passed,
            "status": "registered" if passed else "rejected",
        },
        explainability={
            "purpose": "Register certified replay artifacts for institutional lookup and replay traceability.",
            "read_only_reason": "Registry stores replay metadata only and does not execute or mutate markets.",
            "execution_boundary": "Q Series remains the only execution engine.",
            "contract_adapter": "Accepts OI-189 certification records plus optional OI-187 manifest and OI-188 validation metadata.",
        },
    )

    self._records.append(registration)
    return registration


def _oi190_records(self):
    if not hasattr(self, "_records"):
        self._records = []
    return list(self._records)


UniversalMarketAdapterReplayRegistryEngine.register_certification = _oi190_register_certification
UniversalMarketAdapterReplayRegistryEngine.records = _oi190_records
'''

if "OI-190 GATE 2.1 CONTRACT ADAPTER" not in text190:
    text190 += append190
    OI190.write_text(text190, encoding="utf-8")
    print("[OK] OI-190 register_certification contract adapter appended")
else:
    print("[OK] OI-190 contract adapter already present")

print()
print("[DONE] Gate 2.1 OI-189/OI-190 contract hardening installed")
print()
print("Run:")
print("py test_oi_189_universal_market_adapter_query_replay_certification_engine.py")
print("py test_oi_190_universal_market_adapter_replay_registry_engine.py")
print("py run_oracle_gate2_1_full_replay_registry_test.py")