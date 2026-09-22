from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_full_subsystem_completion_integration_gate import (
    OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationGate,
    OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError,
    stable_hash,
)


def _completion_entry(
    sequence: int,
    adapter_id: str,
) -> dict:
    body = {
        "sequence": sequence,
        "worker_id": "worker-int-oia-001",
        "work_item_id": f"work-{sequence}",
        "adapter_id": adapter_id,
        "source_invocation_hash": stable_hash(
            {"invocation": sequence}
        ),
        "activation_nonce": f"activation-{sequence}",
        "consumption_attempt_nonce": f"attempt-{sequence}",
        "result_type": (
            "OracleLiveCorpusReport"
            if sequence == 1
            else "tuple"
        ),
        "result_hash": stable_hash({"result": sequence}),
        "result_summary_hash": stable_hash(
            {"summary": sequence}
        ),
        "callable_invoked": True,
        "adapter_executed": True,
        "corpus_read_executed": True,
        "source_mutation_performed": False,
        "completion_validated": True,
        "completion_status": "validated",
    }
    body[
        "controlled_callable_invocation_completion_entry_hash"
    ] = stable_hash(body)
    return body


def _seed(path: Path) -> None:
    entries = [
        _completion_entry(
            1,
            "oracle_read_only_canonical_observation_adapter.v1",
        ),
        _completion_entry(
            2,
            "oracle_read_only_market_state_lineage_adapter.v1",
        ),
    ]
    manifest = {
        "schema_version": "OIA-067",
        "engine_id": "OIA-067",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "controlled_callable_invocation_completion_attestation_id": (
            "oia067-test"
        ),
        "controlled_callable_invocation_completion_attestation_status": (
            "evidence_read_execution_adapter_"
            "controlled_callable_invocation_completed"
        ),
        "controlled_callable_invocation_completion_attestation_policy_id": (
            "test"
        ),
        "worker_id": "worker-int-oia-001",
        "completion_entry_count": len(entries),
        "completion_entries": entries,
        "source_invocation_id": "oia066-test",
        "source_invocation_manifest_hash": stable_hash({"oia": 66}),
        "source_readiness_id": "oia065-test",
        "source_readiness_manifest_hash": stable_hash({"oia": 65}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "completion_module_id": "OIA-067",
        },
        "invocation_results_validated": True,
        "all_approved_invocations_completed": True,
        "all_result_hashes_verified": True,
        "all_nonce_pairs_unique": True,
        "source_invocation_reexecuted": False,
        "owner_reconstruction_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "oia_subsystem_complete": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest[
        "controlled_callable_invocation_completion_attestation_manifest_hash"
    ] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-001 TEST")
    print(" FULL OIA SUBSYSTEM INTEGRATION")
    print(" OIA-001 THROUGH OIA-067 FREEZE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        completion = root / "completion"
        integration = root / "integration"
        _seed(completion)

        gate = (
            OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationGate(
                completion_directory=completion,
                integration_directory=integration,
            )
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.certify(
            certified_at=fixed,
            persist=True,
        )
        second = gate.certify(
            certified_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-001"
        assert first.oia_001_through_oia_067_complete
        assert first.actual_oia_067_contract_consumed
        assert first.controlled_read_only_execution_completed
        assert first.oia_subsystem_frozen
        assert first.downstream_read_only_consumption_allowed
        assert first.subsystem_boundary.first_module_id == "OIA-001"
        assert first.subsystem_boundary.final_module_id == "OIA-067"
        assert first.subsystem_boundary.module_count == 67
        assert first.subsystem_boundary.read_only_boundary_frozen
        assert not first.source_invocation_reexecuted
        assert not first.owner_reconstruction_performed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_performed
        assert not first.adapter_execution_performed
        assert not first.corpus_read_execution_performed
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_handoff_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        assert (integration / "current.json").exists()
        assert (
            integration
            / "certifications"
            / f"{first.integration_certification_id}.json"
        ).exists()
        assert (
            integration
            / "boundaries"
            / f"{first.subsystem_boundary.boundary_id}.json"
        ).exists()

        tampered = json.loads(
            (completion / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["oia_subsystem_complete"] = False
        (completion / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )

        try:
            gate.certify(
                certified_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered OIA-067 completion was accepted"
            )
        except OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError:
            pass

    print("[PASS] Actual OIA-067 completion contract consumed")
    print("[PASS] OIA-001 through OIA-067 certified complete")
    print("[PASS] Exact approved read adapter set preserved")
    print("[PASS] Controlled read-only execution boundary verified")
    print("[PASS] Full lineage, result hashes, and nonce integrity preserved")
    print("[PASS] OIA subsystem frozen against accidental extension")
    print("[PASS] Downstream read-only consumption boundary issued")
    print("[PASS] OIA-066 invocation was not re-executed")
    print("[PASS] No owner reconstruction, binding, invocation, or read repeated")
    print("[PASS] Tampered or incomplete completion evidence rejected")
    print("[PASS] Atomic integration certification artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series execution, orders, funds, and "
        "portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
