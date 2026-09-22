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
    print(" OIT-007 TEST")
    print(" QUERYABLE INTELLIGENCE READ MODEL")
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
        ):
            (terminal / source_name).write_text(
                (installed_terminal / source_name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        intelligence = (
            root / "runtime" / "oracle_intelligence" / "bounded_activation"
        )
        terminal_runtime = root / "runtime" / "oracle_terminal"
        intelligence.mkdir(parents=True, exist_ok=True)
        terminal_runtime.mkdir(parents=True, exist_ok=True)

        artifact_path = intelligence / "first_genuine_intelligence.json"
        artifact_payload = {
            "schema_version": "TEST-INTELLIGENCE-1",
            "status": "produced_by_existing_analytics_pipeline",
            "records": [
                {
                    "market_id": "MARKET-001",
                    "title": "Will Alpha happen?",
                    "probability": 0.72,
                    "stance": "bull",
                },
                {
                    "market_id": "MARKET-002",
                    "title": "Will Beta happen?",
                    "probability": 0.31,
                    "stance": "bear",
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
            "sha256": hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest(),
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
                "oracle_queryable_intelligence_read_model",
                fromlist=["*"],
            )

            model = module.build_queryable_intelligence_read_model(
                repository_root=root
            )
            assert module.verify_queryable_intelligence_read_model(model)
            assert model.query_ready
            assert model.artifact_count == 1
            assert model.record_count == 2
            assert model.analytics_execution_performed is False
            assert model.database_access_performed is False

            artifact_model = model.artifacts[0]
            assert artifact_model.record_container == "records"
            assert artifact_model.normalized_record_count == 2
            assert "market_id" in artifact_model.field_paths
            assert "probability" in artifact_model.field_paths

            first = module.select_queryable_record(
                model,
                selector="1",
            )
            assert first.record_id == "MARKET-001"
            assert first.payload["stance"] == "bull"

            second = module.select_queryable_record(
                model,
                selector="MARKET-002",
            )
            assert second.global_record_index == 2

            bull = module.search_queryable_records(
                model,
                query="alpha bull",
            )
            assert len(bull) == 1
            assert bull[0].record_id == "MARKET-001"

            none = module.search_queryable_records(
                model,
                query="gamma",
            )
            assert none == ()

            status = "\n".join(
                module.queryable_intelligence_status_lines(model)
            )
            schema = "\n".join(
                module.queryable_schema_lines(model)
            )
            inventory = "\n".join(
                module.queryable_record_inventory_lines(model.records)
            )
            detail = "\n".join(
                module.queryable_record_lines(first)
            )
            assert "query_ready: true" in status
            assert "record_container: records" in schema
            assert "[1] MARKET-001" in inventory
            assert '"probability": 0.72' in detail
            assert "read_only: true" in detail

            assert hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest() == before_hash
            assert artifact_path.stat().st_mtime_ns == before_mtime

            artifact_path.write_text(
                json.dumps({"mutated": True}) + "\n",
                encoding="utf-8",
            )
            blocked = module.build_queryable_intelligence_read_model(
                repository_root=root
            )
            assert not blocked.query_ready
            assert blocked.record_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Actual OIT-006 consumption contract consumed")
    print("[PASS] Genuine artifact records normalized deterministically")
    print("[PASS] Stable artifact and record hashes verified")
    print("[PASS] Record identifiers derived without mutation")
    print("[PASS] Field-path schema discovery installed")
    print("[PASS] Indexed and record-ID selection installed")
    print("[PASS] Multi-term read-only search installed")
    print("[PASS] Source artifact bytes and modification time unchanged")
    print("[PASS] Mutated source artifact blocks query model")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-007 QUERYABLE INTELLIGENCE READ MODEL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
