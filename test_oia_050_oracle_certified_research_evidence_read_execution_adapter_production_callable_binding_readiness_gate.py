import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_binding_readiness_gate import (
    APPROVED_BINDING_SIGNATURE_REGISTRY,
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableBindingReadinessGate,
    ProductionCallableBindingReadinessInvariantError,
    STATUS_BINDING_READY,
    STATUS_BINDING_READINESS_ISSUED,
    stable_hash,
)


def _hash(label: str) -> str:
    return stable_hash({"source": label})


def _lineage() -> dict:
    return {
        "source_evidence_read_execution_adapter_invocation_manifest_id": "oia041-test",
        "source_evidence_read_execution_adapter_authorization_manifest_id": "oia040-test",
        "source_evidence_read_execution_adapter_readiness_manifest_id": "oia039-test",
        "source_evidence_read_execution_adapter_binding_manifest_id": "oia038-test",
        "source_evidence_read_execution_invocation_activation_id": "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id": "oia036-test",
        "source_evidence_read_execution_authorization_id": "oia035-test",
        "source_evidence_read_execution_readiness_id": "oia034-test",
        "source_evidence_read_request_activation_id": "oia033-test",
        "source_evidence_read_request_manifest_id": "oia032-test",
        "source_evidence_task_activation_id": "oia031-test",
        "source_evidence_task_manifest_id": "oia030-test",
        "source_evidence_batch_activation_id": "oia029-test",
        "source_evidence_batch_id": "oia028-test",
        "source_evidence_session_id": "oia027-test",
        "source_evidence_manifest_id": "oia026-test",
        "source_certification_id": "oia025-test",
        "source_readiness_id": "oia024-test",
        "source_session_id": "oia023-test",
        "source_activation_id": "oia022-test",
        "source_claim_id": "oia021-test",
        "dispatch_manifest_id": "oia020-test",
        "selected_batch_id": "oia020-batch",
        "selected_batch_number": 1,
    }


def _entry(sequence: int, adapter_id: str, config: dict) -> dict:
    body = {
        "sequence": sequence,
        "worker_id": "oracle-worker-test",
        "work_item_id": f"work-{sequence}",
        "adapter_id": adapter_id,
        "read_operation": config["read_operation"],
        "module_path": config["module_path"],
        "owner_name": config["owner_name"],
        "callable_name": config["callable_name"],
        "callable_kind": config["callable_kind"],
        "callable_qualified_name": f"{config['module_path']}.{config['owner_name']}.{config['callable_name']}",
        "module_imported": True,
        "owner_resolved": True,
        "callable_resolved": True,
        "owner_instantiated": False,
        "callable_bound": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "resolution_checks": ["approved_registry_identity_verified"],
        "resolution_status": "evidence_read_execution_adapter_production_callable_resolved",
        "source_active_invocation_execution_authorization_hash": _hash(f"auth-{sequence}"),
        "source_active_invocation_execution_readiness_hash": _hash(f"ready-{sequence}"),
        "source_active_execution_invocation_hash": _hash(f"active-{sequence}"),
        "source_execution_invocation_hash": _hash(f"invoke-{sequence}"),
        "source_authorization_entry_hash": _hash(f"prior-auth-{sequence}"),
        "source_readiness_entry_hash": _hash(f"prior-ready-{sequence}"),
        "source_active_adapter_invocation_hash": _hash(f"adapter-active-{sequence}"),
    }
    body["callable_resolution_hash"] = stable_hash(body)
    return body


def seed(directory: Path) -> dict:
    entries = [
        _entry(sequence, adapter_id, dict(config))
        for sequence, (adapter_id, config) in enumerate(
            APPROVED_BINDING_SIGNATURE_REGISTRY.items(), start=1
        )
    ]
    body = {
        "schema_version": "OIA-049",
        "engine_id": "OIA-049",
        "resolved_at": "2026-07-22T20:00:00+00:00",
        "callable_resolution_id": "oia049-test-resolution",
        "callable_resolution_status": "evidence_read_execution_adapter_production_callable_resolution_issued",
        "callable_resolution_policy_id": "oracle.certified-research-evidence-read-execution-adapter-production-callable-resolution.v1",
        "worker_id": "oracle-worker-test",
        "resolution_entry_count": len(entries),
        "resolution_entries": entries,
        "approved_registry_hash": _hash("registry"),
        "source_execution_authorization_id": "oia048-test",
        "source_execution_authorization_manifest_hash": _hash("oia048"),
        "source_execution_readiness_id": "oia047-test",
        "source_execution_readiness_manifest_hash": _hash("oia047"),
        "source_invocation_activation_id": "oia046-test",
        "source_invocation_activation_manifest_hash": _hash("oia046"),
        "source_execution_invocation_manifest_id": "oia045-test",
        "source_execution_invocation_manifest_hash": _hash("oia045"),
        "source_prior_execution_authorization_id": "oia044-test",
        "source_prior_execution_authorization_manifest_hash": _hash("oia044"),
        "source_prior_execution_readiness_id": "oia043-test",
        "source_prior_execution_readiness_manifest_hash": _hash("oia043"),
        "source_activation_hash": _hash("oia042"),
        "source_lineage": _lineage(),
        "callable_resolution_issued": True,
        "module_import_allowed": True,
        "module_import_performed": True,
        "owner_resolution_allowed": True,
        "owner_resolution_performed": True,
        "callable_resolution_allowed": True,
        "callable_resolution_performed": True,
        "owner_instantiation_allowed": False,
        "owner_instantiation_performed": False,
        "callable_binding_allowed": False,
        "callable_binding_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
        "adapter_execution_allowed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_allowed": False,
        "corpus_read_execution_performed": False,
        "research_execution_allowed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "resolution_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["callable_resolution_manifest_hash"] = stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["resolution_entries"]:
        body = dict(entry)
        body.pop("callable_resolution_hash", None)
        entry["callable_resolution_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("callable_resolution_manifest_hash", None)
    payload["callable_resolution_manifest_hash"] = stable_hash(body)


def reject(gate, evaluated_at, message):
    try:
        gate.evaluate(evaluated_at=evaluated_at, persist=False)
    except ProductionCallableBindingReadinessInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-050 TEST")
    print(" CALLABLE BINDING READINESS")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        resolution = root / "resolution"
        readiness = root / "readiness"
        source = seed(resolution)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableBindingReadinessGate(
            resolution_directory=resolution,
            binding_readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, 21, 0, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-050"
        assert first.engine_id == "OIA-050"
        assert first.callable_binding_readiness_status == STATUS_BINDING_READINESS_ISSUED
        assert first.readiness_entry_count == 2
        assert first.source_callable_resolution_manifest_hash == source["callable_resolution_manifest_hash"]
        assert first.source_lineage == source["source_lineage"]
        by_id = {entry.adapter_id: entry for entry in first.readiness_entries}
        corpus = by_id["oracle_read_only_canonical_observation_adapter.v1"]
        lineage = by_id["oracle_read_only_market_state_lineage_adapter.v1"]
        assert corpus.required_constructor_parameters == ("connection_factory",)
        assert corpus.optional_constructor_parameters == ("stale_after_seconds", "market_limit")
        assert corpus.required_callable_parameters == ()
        assert corpus.optional_callable_parameters == ("inspected_at",)
        assert lineage.required_constructor_parameters == ()
        assert lineage.optional_constructor_parameters == ()
        assert lineage.required_callable_parameters == ()
        assert lineage.optional_callable_parameters == ()
        for entry in first.readiness_entries:
            assert entry.readiness_status == STATUS_BINDING_READY
            assert entry.module_imported is True
            assert entry.owner_resolved is True
            assert entry.callable_resolved is True
            assert entry.signature_inspection_performed is True
            assert entry.owner_instantiated is False
            assert entry.constructor_arguments_bound is False
            assert entry.callable_arguments_bound is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            body = dict(entry.__dict__)
            digest = body.pop("callable_binding_readiness_hash")
            assert digest == stable_hash(body)
        assert first.callable_binding_readiness_issued is True
        assert first.signature_inspection_performed is True
        assert first.owner_instantiation_allowed is False
        assert first.owner_instantiation_performed is False
        assert first.constructor_argument_binding_allowed is False
        assert first.constructor_argument_binding_performed is False
        assert first.callable_argument_binding_allowed is False
        assert first.callable_argument_binding_performed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        assert first.signals_allowed is False
        assert first.alerts_allowed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.market_order_creation_allowed is False
        assert first.funds_movement_allowed is False
        assert first.portfolio_mutation_allowed is False
        body = dict(first.__dict__)
        digest = body.pop("callable_binding_readiness_manifest_hash")
        body["readiness_entries"] = [dict(entry.__dict__) for entry in first.readiness_entries]
        assert digest == stable_hash(body)
        assert (readiness / "current.json").exists()
        assert list((readiness / "readiness").glob("*.json"))
        assert list((readiness / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((resolution / "current.json").read_text(encoding="utf-8"))
        tampered["resolution_entries"][0]["callable_bound"] = True
        rehash(tampered)
        (resolution / "current.json").write_text(json.dumps(tampered, indent=2) + "\n", encoding="utf-8")
        reject(gate, fixed, "Already-bound callable accepted.")

        seed(resolution)
        unknown = json.loads((resolution / "current.json").read_text(encoding="utf-8"))
        unknown["resolution_entries"][0]["adapter_id"] = "oracle_read_only_unknown_adapter.v1"
        rehash(unknown)
        (resolution / "current.json").write_text(json.dumps(unknown, indent=2) + "\n", encoding="utf-8")
        reject(gate, fixed, "Unknown adapter accepted.")

        seed(resolution)
        duplicate = json.loads((resolution / "current.json").read_text(encoding="utf-8"))
        duplicate["resolution_entries"][1]["adapter_id"] = duplicate["resolution_entries"][0]["adapter_id"]
        rehash(duplicate)
        (resolution / "current.json").write_text(json.dumps(duplicate, indent=2) + "\n", encoding="utf-8")
        reject(gate, fixed, "Duplicate adapter accepted.")

        seed(resolution)
        executable = json.loads((resolution / "current.json").read_text(encoding="utf-8"))
        executable["adapter_execution_allowed"] = True
        rehash(executable)
        (resolution / "current.json").write_text(json.dumps(executable, indent=2) + "\n", encoding="utf-8")
        reject(gate, fixed, "Executable manifest accepted.")

    print("[PASS] Actual OIA-049 callable-resolution contract consumed")
    print("[PASS] Actual production constructor and method signatures inspected")
    print("[PASS] Required and optional binding parameters classified deterministically")
    print("[PASS] Binding-readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-049 lineage preserved")
    print("[PASS] Owners were not instantiated and arguments were not bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Unknown, duplicate, bound, or executable input rejected")
    print("[PASS] Atomic callable-binding-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
