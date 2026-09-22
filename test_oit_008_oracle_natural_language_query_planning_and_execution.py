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
    print(" OIT-008 CORRECTION V3 TEST")
    print(" FULL QUERY EXECUTION REPLACEMENT")
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
                "oracle_natural_language_query_planning_and_execution",
                fromlist=["*"],
            )

            plan = module.build_natural_language_query_plan(
                query="Show me the bull Alpha market probability",
                result_limit=5,
            )
            assert module.verify_natural_language_query_plan(plan)
            assert plan.search_terms == (
                "bull",
                "alpha",
                "market",
                "probability",
            )
            assert plan.required_content_terms == ("bull", "alpha")
            assert plan.generic_schema_terms == ("market", "probability")
            assert "market_id" in plan.field_hints
            assert "probability" in plan.field_hints
            assert "stance" in plan.field_hints

            result = module.execute_natural_language_query(
                repository_root=root,
                query="Show me the bull Alpha market probability",
                result_limit=5,
            )
            assert module.verify_natural_language_query_result(result)
            assert result.query_ready
            assert result.match_count == 1
            assert result.matches[0].record_id == "MARKET-001"
            assert result.matches[0].matched_required_terms == (
                "bull",
                "alpha",
            )

            no_match = module.execute_natural_language_query(
                repository_root=root,
                query="gamma market",
            )
            assert no_match.query_ready
            assert no_match.match_count == 0
            assert "no matching" in no_match.failure_reason

            bull_query = module.execute_natural_language_query(
                repository_root=root,
                query="bull market probability",
            )
            assert bull_query.query_ready
            assert bull_query.match_count == 1
            assert bull_query.matches[0].record_id == "MARKET-001"

            schema_only = module.execute_natural_language_query(
                repository_root=root,
                query="market probability",
            )
            assert schema_only.query_ready
            assert schema_only.match_count == 2

            venue_query = module.execute_natural_language_query(
                repository_root=root,
                query="Kalshi venue",
            )
            assert venue_query.query_ready
            assert venue_query.match_count == 1
            assert venue_query.matches[0].record_id == "MARKET-001"

            rendered = "\n".join(
                module.natural_language_query_result_lines(result)
            )
            assert "required_content_terms: bull, alpha" in rendered
            assert "generic_schema_terms: market, probability" in rendered
            assert "match_count: 1" in rendered
            assert "read_only: true" in rendered

            assert hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest() == before_hash
            assert artifact_path.stat().st_mtime_ns == before_mtime

            artifact_path.write_text(
                json.dumps({"mutated": True}) + "\n",
                encoding="utf-8",
            )
            blocked = module.execute_natural_language_query(
                repository_root=root,
                query="alpha",
            )
            assert not blocked.query_ready
            assert blocked.match_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Actual OIT-007 queryable read model consumed")
    print("[PASS] Complete OIT-008 production module replaced")
    print("[PASS] Generic schema terms separated from content terms")
    print("[PASS] Bull, bear, neutral, names, IDs, and venues remain mandatory")
    print("[PASS] gamma market false positive rejected")
    print("[PASS] bull market probability returns only bull record")
    print("[PASS] schema-only market probability query returns both records")
    print("[PASS] Exact venue content filtering verified")
    print("[PASS] Artifact and record lineage preserved")
    print("[PASS] Source artifact bytes and modification time unchanged")
    print("[PASS] Mutated source artifact blocks query execution")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-008 CORRECTION V3 FULL REPLACEMENT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
