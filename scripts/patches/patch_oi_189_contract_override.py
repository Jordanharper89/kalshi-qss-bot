from pathlib import Path

ROOT = Path.cwd()
MODULE = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_query_replay_certification_engine.py"

append = r'''

# ---------------------------------------------------------------------------
# OI-189 CONTRACT ALIGNMENT OVERRIDE
# Aligns OI-189 with OI-188 validation output fields:
# replay_validation_hash, target_manifest_hash, target_chain_hash,
# target_manifest_id, telemetry.entry_count.
# ---------------------------------------------------------------------------

def _oi189_contract_safe_dict(value):
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, dict):
            return converted
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    if isinstance(value, dict):
        return dict(value)
    return {"value": value}


def _oi189_contract_hash(value):
    import json
    from hashlib import sha256
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _oi189_contract_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _oi189_contract_certify_validation(self, validation_result, manifest=None, certification_context=None):
    data = _oi189_contract_safe_dict(validation_result)
    manifest_data = _oi189_contract_safe_dict(manifest)
    context = _oi189_contract_safe_dict(certification_context)

    validation_id = str(data.get("validation_id") or "")
    validation_hash = str(
        data.get("validation_hash")
        or data.get("replay_validation_hash")
        or data.get("validation_result_hash")
        or ""
    )
    manifest_id = str(
        manifest_data.get("manifest_id")
        or data.get("manifest_id")
        or data.get("target_manifest_id")
        or ""
    )
    manifest_hash = str(
        manifest_data.get("manifest_hash")
        or data.get("manifest_hash")
        or data.get("target_manifest_hash")
        or ""
    )
    chain_hash = str(
        manifest_data.get("chain_hash")
        or data.get("chain_hash")
        or data.get("target_chain_hash")
        or ""
    )
    entry_count = int(
        manifest_data.get("entry_count")
        or data.get("entry_count")
        or _oi189_contract_safe_dict(data.get("telemetry")).get("entry_count")
        or 0
    )
    validation_passed = bool(data.get("passed") is True)

    findings = []

    if not validation_passed:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_NOT_PASSED",
            severity="critical",
            message="Replay validation did not pass certification precondition.",
            evidence={"validation_passed": validation_passed},
        ))

    if len(validation_hash) != 64:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_HASH_INVALID",
            severity="error",
            message="Validation hash must be a 64-character digest.",
            evidence={"validation_hash": validation_hash},
        ))

    if len(manifest_hash) != 64:
        findings.append(ReplayCertificationFinding(
            code="MANIFEST_HASH_INVALID",
            severity="error",
            message="Manifest hash must be a 64-character digest.",
            evidence={"manifest_hash": manifest_hash},
        ))

    if len(chain_hash) != 64:
        findings.append(ReplayCertificationFinding(
            code="CHAIN_HASH_INVALID",
            severity="error",
            message="Chain hash must be a 64-character digest.",
            evidence={"chain_hash": chain_hash},
        ))

    guardrails = _oi189_contract_safe_dict(data.get("read_only_guardrails"))
    for key, expected in READ_ONLY_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            findings.append(ReplayCertificationFinding(
                code="READ_ONLY_GUARDRAIL_MISMATCH",
                severity="critical",
                message="Certification requires Oracle read-only guardrails.",
                evidence={"key": key, "expected": expected, "actual": guardrails.get(key)},
            ))

    source_findings = data.get("findings") or []
    if source_findings:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_FINDINGS_PRESENT",
            severity="info",
            message="Validation included non-blocking findings that remain visible in certification.",
            evidence={"validation_finding_count": len(source_findings)},
        ))

    blocker_count = sum(1 for f in findings if f.severity in {"critical", "error"})
    warning_count = sum(1 for f in findings if f.severity in {"warning", "info"})

    certified = blocker_count == 0
    if not certified:
        certification_level = "not_certified"
    elif warning_count:
        certification_level = "certified_with_warnings"
    else:
        certification_level = "certified"

    payload = {
        "oracle_instance_id": self.oracle_instance_id,
        "validation_id": validation_id,
        "validation_hash": validation_hash,
        "manifest_id": manifest_id,
        "manifest_hash": manifest_hash,
        "chain_hash": chain_hash,
        "entry_count": entry_count,
        "certified": certified,
        "certification_level": certification_level,
        "findings": [f.to_dict() for f in findings],
        "context": context,
    }
    certification_hash = _oi189_contract_hash(payload)

    record = ReplayCertificationRecord(
        certification_id="oi189.certification." + certification_hash[:24],
        created_at=_oi189_contract_now(),
        oracle_instance_id=self.oracle_instance_id,
        module_id=self.module_id,
        module_name=self.module_name,
        validation_id=validation_id,
        validation_hash=validation_hash,
        manifest_id=manifest_id,
        manifest_hash=manifest_hash,
        chain_hash=chain_hash,
        entry_count=entry_count,
        validation_passed=validation_passed,
        certified=certified,
        certification_level=certification_level,
        blocker_count=blocker_count,
        warning_count=warning_count,
        certification_hash=certification_hash,
        read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        findings=findings,
        telemetry={
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "entry_count": entry_count,
            "certified": certified,
            "certification_level": certification_level,
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "finding_count": len(findings),
        },
        explainability={
            "purpose": "Certify replay validation results for institutional registry and governance readiness.",
            "read_only_reason": "Certification evaluates metadata only and does not execute or mutate markets.",
            "execution_boundary": "Q Series remains the only execution engine.",
            "contract_alignment": "OI-189 accepts OI-188 canonical fields and target_* replay fields.",
        },
    )

    self._records.append(record)
    return record


UniversalMarketAdapterQueryReplayCertificationEngine.certify_validation = _oi189_contract_certify_validation
'''

text = MODULE.read_text(encoding="utf-8")

if "OI-189 CONTRACT ALIGNMENT OVERRIDE" not in text:
    text += append
    MODULE.write_text(text, encoding="utf-8")
    print("[OK] OI-189 contract override appended")
else:
    print("[OK] OI-189 contract override already present")

print("Run:")
print("py test_oi_189_universal_market_adapter_query_replay_certification_engine.py")
print("py run_oracle_gate2_1_full_replay_registry_test.py")