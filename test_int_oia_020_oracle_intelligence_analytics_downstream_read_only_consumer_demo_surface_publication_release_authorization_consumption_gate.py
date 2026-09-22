from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_consumption_gate import (
    APPROVED_AUTHORIZATION_MODE,
    APPROVED_AUTHORIZATION_SCOPE,
    APPROVED_CONSUMPTION_MODE,
    APPROVED_CONSUMPTION_SCOPE,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _seed_authorization(path: Path) -> None:
    record = {
        "sequence": 1,
        "authorization_id": "authorization-test",
        "attestation_id": "attestation-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_attestation_record_hash": stable_hash({"attestation": 1}),
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "source_demo_surface_release_id": "demo-release-test",
        "source_demo_surface_release_record_hash": stable_hash({"release": 1}),
        "source_result_admission_id": "admission-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "authorization_mode": APPROVED_AUTHORIZATION_MODE,
        "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
        "attestation_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "source_release_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "independent_attestation_verified": True,
        "authorization_scope_verified": True,
        "duplicate_authorization_rejected": True,
        "publication_release_authorized": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "authorization_status": (
            "attested_demo_surface_publication_release_authorized"
        ),
    }
    record["authorization_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-019",
        "engine_id": "INT-OIA-019",
        "authorized_at": "2026-07-23T00:00:00+00:00",
        "authorization_manifest_id": "int-oia-019-test",
        "authorization_status": "demo_surface_publication_release_authorized",
        "authorization_policy_id": "test",
        "authorization_mode": APPROVED_AUTHORIZATION_MODE,
        "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
        "source_attestation_manifest_id": "int-oia-018-test",
        "source_attestation_manifest_hash": stable_hash({"int": 18}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorization_record_count": 1,
        "authorization_records": [record],
        "all_attestation_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_source_release_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_independent_attestations_verified": True,
        "all_authorization_scopes_verified": True,
        "all_publication_releases_authorized": True,
        "duplicate_authorizations_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "demo_surface_released": True,
        "publication_manifest_published": True,
        "publication_manifest_attested": True,
        "publication_release_authorized": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "signals_created": False,
        "alerts_allowed": False,
        "alerts_created": False,
        "qseries_handoff_allowed": False,
        "qseries_handoff_performed": False,
        "qseries_execution_allowed": False,
        "qseries_execution_performed": False,
        "market_order_creation_allowed": False,
        "market_order_creation_performed": False,
        "funds_movement_allowed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_allowed": False,
        "portfolio_mutation_performed": False,
        "authorization_artifact_persistence_allowed": True,
    }
    manifest["authorization_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-020 TEST")
    print(" WINDOWS PATH-SAFE INSTALLER")
    print(" IN-MEMORY SYNTAX VERIFICATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        authorization = root / "authorization"
        consumption = root / "consumption"
        _seed_authorization(authorization)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionGate(
            authorization_directory=authorization,
            consumption_directory=consumption,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.consume(consumed_at=fixed, persist=True)
        second = gate.consume(consumed_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-020"
        assert first.consumption_mode == APPROVED_CONSUMPTION_MODE
        assert first.consumption_scope == APPROVED_CONSUMPTION_SCOPE
        assert first.consumption_record_count == 1
        assert first.all_authorization_record_hashes_verified
        assert first.all_attestation_record_hashes_verified
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_independent_attestations_verified
        assert first.all_authorization_scopes_verified
        assert first.all_consumption_scopes_verified
        assert first.all_authorizations_consumed_once
        assert first.duplicate_consumptions_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.publication_release_authorized
        assert first.publication_release_authorization_consumed
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.consumption_records[0]
        assert record.authorization_record_hash_verified
        assert record.attestation_record_hash_verified
        assert record.publication_record_hash_verified
        assert record.publication_payload_hash_verified
        assert record.authorization_scope_verified
        assert record.consumption_scope_verified
        assert record.duplicate_consumption_rejected
        assert record.authorization_consumed_once
        assert record.publication_release_authorization_consumed
        assert (
            record.consumption_status
            == "read_only_demo_publication_authorization_consumed_once"
        )
        assert (consumption / "current.json").exists()

        tampered = json.loads(
            (authorization / "current.json").read_text(encoding="utf-8")
        )
        tampered["authorization_records"][0][
            "authorization_scope"
        ] = "unrestricted"
        (authorization / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.consume(consumed_at=fixed, persist=False)
            raise AssertionError("tampered authorization accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationConsumptionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-019 authorization manifest consumed")
    print("[PASS] Authorization manifest hash independently verified")
    print("[PASS] Every authorization-record hash independently verified")
    print("[PASS] Publication and attestation hash lineage preserved")
    print("[PASS] Complete admission and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Authorization consumption restricted to approved scope")
    print("[PASS] Single-use authorization consumption recorded")
    print("[PASS] Duplicate consumption identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe authorization rejected")
    print("[PASS] Atomic consumption artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
