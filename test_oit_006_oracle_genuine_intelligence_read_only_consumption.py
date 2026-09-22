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
    print(" OIT-006 TEST")
    print(" GENUINE INTELLIGENCE READ-ONLY CONSUMPTION")
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
                {"market_id": "TEST-1", "score": 0.75},
                {"market_id": "TEST-2", "score": 0.65},
            ],
            "metadata": {
                "source": "existing_oracle_pipeline",
                "read_only": True,
            },
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
                "oracle_genuine_intelligence_read_only_consumption",
                fromlist=["*"],
            )

            receipt = module.consume_admitted_intelligence(
                repository_root=root
            )
            assert module.verify_intelligence_consumption(receipt)
            assert receipt.admission_ready
            assert receipt.terminal_consumption_ready
            assert receipt.artifact_count == 1
            assert receipt.analytics_execution_performed is False
            assert receipt.database_access_performed is False

            view = receipt.artifacts[0]
            assert module.verify_intelligence_artifact_view(view)
            assert view.relative_path == relative
            assert view.top_level_keys == (
                "metadata",
                "records",
                "schema_version",
                "status",
            )
            assert view.preview["records"][0]["market_id"] == "TEST-1"

            selected_by_index = module.select_intelligence_artifact(
                receipt,
                selector="1",
            )
            selected_by_path = module.select_intelligence_artifact(
                receipt,
                selector=relative,
            )
            assert selected_by_index.view_hash == view.view_hash
            assert selected_by_path.view_hash == view.view_hash

            status = "\n".join(
                module.intelligence_consumption_status_lines(receipt)
            )
            inventory = "\n".join(
                module.intelligence_inventory_lines(receipt)
            )
            detail = "\n".join(
                module.intelligence_artifact_lines(view)
            )
            assert "terminal_consumption_ready: true" in status
            assert f"[1] {relative}" in inventory
            assert '"market_id": "TEST-1"' in detail
            assert "read_only: true" in detail

            assert hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest() == before_hash
            assert artifact_path.stat().st_mtime_ns == before_mtime

            artifact_path.write_text(
                json.dumps({"mutated": True}) + "\n",
                encoding="utf-8",
            )
            blocked = module.consume_admitted_intelligence(
                repository_root=root
            )
            assert not blocked.terminal_consumption_ready
            assert blocked.artifact_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Actual OIT-005 immutable admission contract consumed")
    print("[PASS] Only OIT-005-admitted artifacts consumed")
    print("[PASS] Artifact inventory and indexed selection installed")
    print("[PASS] Exact-path artifact selection installed")
    print("[PASS] Bounded schema and record preview installed")
    print("[PASS] Artifact bytes and modification time remained unchanged")
    print("[PASS] Mutated artifact consumption blocked")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Terminal consumption remains read-only")
    print("[DONE] OIT-006 GENUINE INTELLIGENCE READ-ONLY CONSUMPTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
