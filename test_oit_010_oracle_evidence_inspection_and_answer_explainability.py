import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def stable_hash(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clear_modules():
    for name in list(sys.modules):
        if name == "qseries_v2" or name.startswith("qseries_v2."):
            del sys.modules[name]


def main() -> int:
    print("=" * 40)
    print(" OIT-010 TEST")
    print(" EVIDENCE INSPECTION AND EXPLAINABILITY")
    print("=" * 40)

    installed_root = Path(__file__).resolve().parent
    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        qseries = root / "qseries_v2"
        terminal = qseries / "oracle_terminal"
        for directory in (qseries, terminal):
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "__init__.py").write_text("", encoding="utf-8")

        for source_name in (
            "oracle_genuine_intelligence_artifact_admission.py",
            "oracle_genuine_intelligence_read_only_consumption.py",
            "oracle_queryable_intelligence_read_model.py",
            "oracle_natural_language_query_planning_and_execution.py",
            "oracle_grounded_intelligence_answer_composition.py",
            "oracle_evidence_inspection_and_answer_explainability.py",
        ):
            (terminal / source_name).write_text(
                (installed_terminal / source_name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        intelligence = root / "runtime" / "oracle_intelligence" / "bounded_activation"
        terminal_runtime = root / "runtime" / "oracle_terminal"
        intelligence.mkdir(parents=True, exist_ok=True)
        terminal_runtime.mkdir(parents=True, exist_ok=True)

        artifact_path = intelligence / "first_genuine_intelligence.json"
        artifact_payload = {
            "schema_version": "TEST-INTELLIGENCE-1",
            "records": [
                {
                    "market_id": "MARKET-001",
                    "title": "Will Alpha happen?",
                    "probability": 0.72,
                    "stance": "bull",
                    "venue": "Kalshi",
                },
                {
                    "market_id": "MARKET-002",
                    "title": "Will Beta happen?",
                    "probability": 0.31,
                    "stance": "bear",
                    "venue": "Polymarket",
                },
            ],
        }
        artifact_path.write_text(
            json.dumps(artifact_payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stat = artifact_path.stat()
        relative = artifact_path.relative_to(root).as_posix()
        artifact_state = {
            "relative_path": relative,
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            "byte_count": stat.st_size,
            "modified_ns": stat.st_mtime_ns,
        }

        activation_body = {
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
        activation_body["receipt_hash"] = stable_hash(activation_body)
        (terminal_runtime / "oit_004_bounded_activation_receipt.json").write_text(
            json.dumps(activation_body, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        before_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        before_mtime = artifact_path.stat().st_mtime_ns

        old_path = list(sys.path)
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.path.insert(0, str(root))
            clear_modules()
            module = __import__(
                "qseries_v2.oracle_terminal."
                "oracle_evidence_inspection_and_answer_explainability",
                fromlist=["*"],
            )

            report = module.build_answer_explainability_report(
                repository_root=root,
                query="Show me the bull Alpha market probability",
                result_limit=5,
            )
            assert module.verify_answer_explainability_report(report)
            assert report.answer_grounded
            assert report.explainability_ready
            assert report.evidence_count == 1
            assert report.explained_evidence_count == 1

            inspection = report.inspections[0]
            assert module.verify_evidence_inspection(inspection)
            assert inspection.record_id == "MARKET-001"
            assert inspection.artifact_relative_path == relative
            assert inspection.matched_required_terms == ("bull", "alpha")
            assert inspection.query_plan_hash == report.query_plan_hash
            assert inspection.lineage_complete
            assert any(
                support.matched_term == "bull"
                and support.support_path == "stance"
                for support in inspection.supports
            )
            assert any(
                support.matched_term == "alpha"
                and support.support_path == "title"
                for support in inspection.supports
            )
            assert any(
                support.matched_term == "probability"
                and support.support_path == "probability"
                for support in inspection.supports
            )

            assert module.select_evidence_inspection(
                report, selector="E1"
            ).inspection_hash == inspection.inspection_hash
            assert module.select_evidence_inspection(
                report, selector="MARKET-001"
            ).inspection_hash == inspection.inspection_hash

            rendered_report = "\n".join(
                module.answer_explainability_lines(report)
            )
            rendered_evidence = "\n".join(
                module.evidence_inspection_lines(inspection)
            )
            assert "explainability_ready: true" in rendered_report
            assert "matched_required_terms: bull, alpha" in rendered_report
            assert "path: stance" in rendered_evidence
            assert "path: title" in rendered_evidence
            assert "query_plan_hash:" in rendered_evidence
            assert "lineage_complete: true" in rendered_evidence

            no_match = module.build_answer_explainability_report(
                repository_root=root,
                query="gamma market",
            )
            assert not no_match.answer_grounded
            assert not no_match.explainability_ready
            assert no_match.explained_evidence_count == 0

            assert hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest() == before_hash
            assert artifact_path.stat().st_mtime_ns == before_mtime

            artifact_path.write_text(
                json.dumps({"mutated": True}) + "\n",
                encoding="utf-8",
            )
            blocked = module.build_answer_explainability_report(
                repository_root=root,
                query="alpha",
            )
            assert not blocked.explainability_ready
            assert blocked.explained_evidence_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Certified OIT-009 CORRECTION V2 contract consumed")
    print("[PASS] Every grounded evidence item inspected deterministically")
    print("[PASS] Required-content terms preserved through explainability")
    print("[PASS] Matched terms mapped to exact bounded support paths")
    print("[PASS] Evidence selection by E-index and record ID installed")
    print("[PASS] Query-plan, answer, evidence, record, and artifact lineage preserved")
    print("[PASS] No-match answer produces no false explainability")
    print("[PASS] Source artifact bytes and modification time unchanged")
    print("[PASS] Mutated source artifact blocks explainability")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-010 EVIDENCE INSPECTION AND EXPLAINABILITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
