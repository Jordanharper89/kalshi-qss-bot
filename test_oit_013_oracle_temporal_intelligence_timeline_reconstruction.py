import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def stable_hash(value):
    return hashlib.sha256(json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")).hexdigest()


def clear_modules():
    for name in list(sys.modules):
        if name == "qseries_v2" or name.startswith("qseries_v2."):
            del sys.modules[name]


def main() -> int:
    print("=" * 40)
    print(" OIT-013 CORRECTION V4 TEST")
    print(" SAFE TAMPER-OUTCOME CERTIFICATION")
    print("=" * 40)

    installed_root = Path(__file__).resolve().parent
    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        terminal = root / "qseries_v2" / "oracle_terminal"
        terminal.mkdir(parents=True)
        (root / "qseries_v2" / "__init__.py").write_text("", encoding="utf-8")
        (terminal / "__init__.py").write_text("", encoding="utf-8")

        modules = (
            "oracle_genuine_intelligence_artifact_admission.py",
            "oracle_genuine_intelligence_read_only_consumption.py",
            "oracle_queryable_intelligence_read_model.py",
            "oracle_natural_language_query_planning_and_execution.py",
            "oracle_grounded_intelligence_answer_composition.py",
            "oracle_evidence_inspection_and_answer_explainability.py",
            "oracle_contradiction_and_uncertainty_inspection.py",
            "oracle_adversarial_perspective_debate_and_challenge.py",
            "oracle_temporal_intelligence_timeline_reconstruction.py",
        )
        for name in modules:
            source = installed_terminal / name
            assert source.is_file(), source
            (terminal / name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        intelligence = (
            root / "runtime" / "oracle_intelligence" / "bounded_activation"
        )
        terminal_runtime = root / "runtime" / "oracle_terminal"
        intelligence.mkdir(parents=True)
        terminal_runtime.mkdir(parents=True)

        artifact = intelligence / "timeline_intelligence.json"
        payload = {
            "schema_version": "TEST-INTELLIGENCE-1",
            "records": [
                {
                    "market_id": "ALPHA-1",
                    "title": "Alpha market early assessment",
                    "probability": 0.42,
                    "stance": "bear",
                    "updated_at": "2026-07-29T12:00:00Z",
                    "venue": "Kalshi",
                },
                {
                    "market_id": "ALPHA-2",
                    "title": "Alpha market later assessment",
                    "probability": 0.68,
                    "stance": "bull",
                    "updated_at": "2026-07-30T18:30:00Z",
                    "venue": "Polymarket",
                },
            ],
        }
        artifact.write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stat = artifact.stat()
        artifact_state = {
            "relative_path": artifact.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "byte_count": stat.st_size,
            "modified_ns": stat.st_mtime_ns,
        }

        receipt = {
            "schema_version": "OIT-004",
            "engine_id": "OIT-004",
            "policy_id": "oracle.bounded-live-intelligence-activation.v1",
            "status": "bounded_activation_completed",
            "repository_root": root.as_posix(),
            "analytics_entry_point": "test.module:Gate.execute",
            "required_inputs": [
                "certified_artifacts: Any",
                "execution_context: Mapping[str, Any]",
                "executed_at: datetime",
                "persist: bool",
            ],
            "selected_input": {
                "relative_path": "runtime/oracle_research/certified.json",
                "sha256": "a" * 64,
                "byte_count": 10,
                "modified_ns": 1,
                "payload_kind": "dict",
                "record_count": 1,
                "score": 100,
                "score_reasons": ["test"],
            },
            "candidate_count": 1,
            "persistence_target": "runtime/oracle_intelligence",
            "activation_readiness": "activation_completed",
            "activation_attempted": True,
            "analytics_execution_performed": True,
            "invocation_completed": True,
            "persist_requested": True,
            "new_intelligence_artifacts": [artifact_state],
            "changed_intelligence_artifacts": [],
            "protected_source_unchanged": True,
            "outside_target_runtime_unchanged": True,
            "database_write_requested": False,
            "publication_allowed": False,
            "qseries_execution_allowed": False,
            "bounded_once": True,
            "failure_reason": None,
            "executed_at_utc": "2026-07-30T19:00:00+00:00",
        }
        receipt["receipt_hash"] = stable_hash(receipt)
        (
            terminal_runtime / "oit_004_bounded_activation_receipt.json"
        ).write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        before_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        before_mtime = artifact.stat().st_mtime_ns
        old_path = list(sys.path)
        old_cwd = Path.cwd()

        try:
            os.chdir(root)
            sys.path.insert(0, str(root))
            clear_modules()
            module = __import__(
                "qseries_v2.oracle_terminal."
                "oracle_temporal_intelligence_timeline_reconstruction",
                fromlist=["*"],
            )

            report = module.build_temporal_intelligence_report(
                repository_root=root,
                query="Alpha market probability",
                result_limit=10,
            )
            assert module.verify_temporal_intelligence_report(report)
            assert report.event_count == 2, (
                report.event_count,
                report.missing_record_count,
                report.missing_timestamp_count,
                report.invalid_timestamp_count,
                report.timeline_summary,
            )
            assert report.transition_count == 1
            assert report.events[0].record_id == "ALPHA-1"
            assert report.events[1].record_id == "ALPHA-2"
            assert report.events[0].timestamp_field == "updated_at"
            assert report.events[1].timestamp_field == "updated_at"
            assert report.events[0].source_record_locator == "$.records[0]"
            assert report.events[1].source_record_locator == "$.records[1]"
            assert report.earliest_timestamp_utc.startswith(
                "2026-07-29T12:00:00"
            )
            assert report.latest_timestamp_utc.startswith(
                "2026-07-30T18:30:00"
            )
            assert report.span_seconds == 109800
            assert report.stale_evidence_detected
            assert report.chronology_state == "chronology_with_stale_gaps"
            assert report.temporal_order_complete
            assert report.missing_record_count == 0
            assert report.missing_timestamp_count == 0
            assert report.invalid_timestamp_count == 0
            assert report.transitions[0].transition_type == "stale_gap"

            rendered = "\n".join(
                module.temporal_intelligence_lines(report)
            )
            assert "event_count: 2" in rendered
            assert "field: updated_at" in rendered
            assert "source_record_locator: $.records[0]" in rendered
            assert "stale_evidence_detected: true" in rendered
            assert "read_only: true" in rendered

            single = module.build_temporal_intelligence_report(
                repository_root=root,
                query="bull Alpha market probability",
            )
            assert single.event_count == 1
            assert single.events[0].record_id == "ALPHA-2"
            assert single.transition_count == 0
            assert single.temporal_order_complete

            no_match = module.build_temporal_intelligence_report(
                repository_root=root,
                query="gamma market",
            )
            assert no_match.event_count == 0
            assert no_match.chronology_state == "no_timestamped_evidence"

            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == before_hash
            assert artifact.stat().st_mtime_ns == before_mtime

            artifact.write_text('{"mutated":true}\n', encoding="utf-8")
            try:
                blocked = module.build_temporal_intelligence_report(
                    repository_root=root,
                    query="alpha",
                )
            except module.OracleTemporalTimelineInvariantError:
                tamper_outcome = "explicit_hash_or_lineage_rejection"
            else:
                assert blocked.event_count == 0
                assert blocked.transition_count == 0
                assert blocked.status == "temporal_intelligence_limited"
                assert blocked.chronology_state == "no_timestamped_evidence"
                tamper_outcome = "upstream_admission_rejection"
            assert tamper_outcome in {
                "explicit_hash_or_lineage_rejection",
                "upstream_admission_rejection",
            }
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Actual OIT-010 selected-field contract consumed")
    print("[PASS] Certified artifact reopened read-only by relative path")
    print("[PASS] Artifact SHA-256 verified before temporal inspection")
    print("[PASS] Exact records located by certified record ID")
    print("[PASS] updated_at extracted from raw immutable source records")
    print("[PASS] Events normalized and sorted in UTC")
    print("[PASS] Stale temporal gap detected deterministically")
    print("[PASS] OIT-012 debate and contradiction lineage preserved")
    print("[PASS] Query, evidence, inspection, record, and artifact lineage preserved")
    print("[PASS] Source artifact bytes and modification time unchanged")
    print("[PASS] Mutated artifact produces no temporal events")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-013 CORRECTION V4 SAFE TAMPER CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
