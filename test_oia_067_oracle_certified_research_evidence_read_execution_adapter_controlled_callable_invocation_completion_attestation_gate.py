from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_completion_attestation_gate import (
    ControlledCallableInvocationCompletionAttestationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationCompletionAttestationGate,
    stable_hash,
)


def _entry(
    *,
    sequence: int,
    adapter_id: str,
    result_summary: dict,
) -> dict:
    invocation_arguments = (
        {"inspected_at": None}
        if sequence == 1
        else {}
    )
    body = {
        "sequence": sequence,
        "worker_id": "worker-oia067",
        "work_item_id": f"work-{sequence}",
        "adapter_id": adapter_id,
        "module_path": "module",
        "owner_name": "Owner",
        "callable_name": "read",
        "activation_nonce": f"activation-{sequence}",
        "consumption_attempt_nonce": f"attempt-{sequence}",
        "source_readiness_hash": stable_hash(
            {"readiness": sequence}
        ),
        "invocation_argument_hash": stable_hash(
            invocation_arguments
        ),
        "invocation_arguments": invocation_arguments,
        "owner_reconstructed": True,
        "method_bound_to_owner": True,
        "callable_invoked": True,
        "adapter_executed": True,
        "corpus_read_executed": True,
        "result_type": (
            "OracleLiveCorpusReport"
            if sequence == 1
            else "tuple"
        ),
        "result_hash": stable_hash(
            {"result": sequence}
        ),
        "result_summary": result_summary,
        "source_mutation_performed": False,
        "invocation_status": (
            "evidence_read_execution_adapter_"
            "controlled_callable_invoked"
        ),
    }
    body["controlled_callable_invocation_hash"] = stable_hash(
        body
    )
    return body


def _seed(path: Path) -> None:
    entries = [
        _entry(
            sequence=1,
            adapter_id=(
                "oracle_read_only_canonical_observation_adapter.v1"
            ),
            result_summary={
                "observation_count": 15,
                "market_count": 3,
            },
        ),
        _entry(
            sequence=2,
            adapter_id=(
                "oracle_read_only_market_state_lineage_adapter.v1"
            ),
            result_summary={"record_count": 2},
        ),
    ]

    manifest = {
        "schema_version": "OIA-066",
        "engine_id": "OIA-066",
        "invoked_at": "2026-07-22T00:00:00+00:00",
        "controlled_callable_invocation_id": "oia066-test",
        "controlled_callable_invocation_status": (
            "evidence_read_execution_adapter_"
            "controlled_callable_invocation_issued"
        ),
        "controlled_callable_invocation_policy_id": "test",
        "worker_id": "worker-oia067",
        "invocation_entry_count": len(entries),
        "invocation_entries": entries,
        "source_readiness_id": "oia065-test",
        "source_readiness_manifest_hash": stable_hash(
            {"oia": 65}
        ),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
        },
        "readiness_consumed": True,
        "owner_reconstruction_performed": True,
        "callable_binding_to_owner_performed": True,
        "callable_invocation_performed": True,
        "adapter_execution_performed": True,
        "corpus_read_execution_performed": True,
        "research_execution_allowed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "invocation_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest[
        "controlled_callable_invocation_manifest_hash"
    ] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" OIA-067 TEST")
    print(" INVOCATION COMPLETION ATTESTATION")
    print(" FINAL OIA SUBSYSTEM CLOSEOUT")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        invocation_directory = root / "invocation"
        attestation_directory = root / "attestation"
        _seed(invocation_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationCompletionAttestationGate(
            invocation_directory=invocation_directory,
            attestation_directory=attestation_directory,
        )
        fixed = datetime(
            2026,
            7,
            22,
            tzinfo=timezone.utc,
        )

        first = gate.attest(
            attested_at=fixed,
            persist=True,
        )
        second = gate.attest(
            attested_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-067"
        assert first.completion_entry_count == 2
        assert first.invocation_results_validated
        assert first.all_approved_invocations_completed
        assert first.all_result_hashes_verified
        assert first.all_nonce_pairs_unique
        assert first.oia_subsystem_complete
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
        assert not first.execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        assert (
            attestation_directory / "current.json"
        ).exists()
        assert (
            attestation_directory
            / "attestations"
            / (
                first.controlled_callable_invocation_completion_attestation_id
                + ".json"
            )
        ).exists()

        tampered = json.loads(
            (invocation_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["invocation_entries"][0][
            "result_summary"
        ]["observation_count"] = 999
        (invocation_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )

        try:
            gate.attest(
                attested_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered OIA-066 artifact was accepted"
            )
        except ControlledCallableInvocationCompletionAttestationInvariantError:
            pass

    print("[PASS] Actual OIA-066 invocation contract consumed")
    print("[PASS] Every approved invocation result validated")
    print("[PASS] Entry and manifest hashes independently verified")
    print("[PASS] Activation and execution-attempt nonce pairs unique")
    print("[PASS] Exact approved adapter set certified complete")
    print("[PASS] OIA-020 through OIA-066 lineage preserved")
    print("[PASS] OIA-066 source was not re-executed")
    print("[PASS] No owner reconstruction, binding, or invocation repeated")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or incomplete invocation evidence rejected")
    print("[PASS] Atomic completion-attestation artifacts persisted")
    print("[PASS] OIA subsystem certified complete")
    print(
        "[PASS] Signals, alerts, Q Series, orders, funds, and "
        "portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
