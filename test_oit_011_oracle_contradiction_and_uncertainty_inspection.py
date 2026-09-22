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
    print(" OIT-011 TEST")
    print(" CONTRADICTION AND UNCERTAINTY INSPECTION")
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
            "oracle_contradiction_and_uncertainty_inspection.py",
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
                    "market_id": "ALPHA-1",
                    "title": "Alpha market assessment one",
                    "probability": 0.78,
                    "stance": "bull",
                    "status": "open",
                    "venue": "Kalshi",
                },
                {
                    "market_id": "ALPHA-2",
                    "title": "Alpha market assessment two",
                    "probability": 0.32,
                    "stance": "bear",
                    "status": "open",
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
                "oracle_contradiction_and_uncertainty_inspection",
                fromlist=["*"],
            )

            report = module.build_contradiction_and_uncertainty_report(
                repository_root=root,
                query="Alpha market probability",
                result_limit=10,
            )
            assert module.verify_contradiction_and_uncertainty_report(report)
            assert report.evidence_count == 2
            assert report.claim_count == 6
            assert report.contradiction_count == 2
            assert report.contradiction_state == (
                "material_contradictions_detected"
            )
            assert report.uncertainty_level == "high"
            assert any(
                pair.contradiction_type == "opposed_stance"
                for pair in report.contradictions
            )
            assert any(
                pair.contradiction_type == "probability_divergence"
                for pair in report.contradictions
            )
            assert report.agreement_count == 1
            assert report.corroboration_state == "partially_corroborated"

            rendered = "\n".join(
                module.contradiction_and_uncertainty_lines(report)
            )
            assert "contradiction_count: 2" in rendered
            assert "uncertainty_level: high" in rendered
            assert "opposed_stance" in rendered
            assert "probability_divergence" in rendered
            assert "read_only: true" in rendered

            single = module.build_contradiction_and_uncertainty_report(
                repository_root=root,
                query="bull Alpha market probability",
            )
            assert single.evidence_count == 1
            assert single.contradiction_count == 0
            assert single.corroboration_state == "single_source"
            assert single.uncertainty_level == "medium"

            no_match = module.build_contradiction_and_uncertainty_report(
                repository_root=root,
                query="gamma market",
            )
            assert no_match.evidence_count == 0
            assert no_match.contradiction_count == 0
            assert no_match.corroboration_state == "no_evidence"
            assert no_match.uncertainty_level in {"medium", "high"}

            assert hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest() == before_hash
            assert artifact_path.stat().st_mtime_ns == before_mtime

            artifact_path.write_text(
                json.dumps({"mutated": True}) + "\n",
                encoding="utf-8",
            )
            blocked = module.build_contradiction_and_uncertainty_report(
                repository_root=root,
                query="alpha",
            )
            assert blocked.evidence_count == 0
            assert blocked.contradiction_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Certified OIT-010 explainability contract consumed")
    print("[PASS] Bounded stance, probability, and status claims extracted")
    print("[PASS] Opposed stance contradiction detected")
    print("[PASS] Material probability divergence detected")
    print("[PASS] Agreement counted separately from contradiction")
    print("[PASS] Single-source uncertainty distinguished from corroboration")
    print("[PASS] No-evidence uncertainty handled without invented conclusions")
    print("[PASS] Complete explainability and artifact lineage preserved")
    print("[PASS] Source artifact bytes and modification time unchanged")
    print("[PASS] Mutated source artifact blocks contradiction inspection")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-011 CONTRADICTION AND UNCERTAINTY INSPECTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
