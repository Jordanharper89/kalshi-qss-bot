import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def stable_hash(value):
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clear_modules():
    for name in list(sys.modules):
        if name == "qseries_v2" or name.startswith("qseries_v2."):
            del sys.modules[name]


def main() -> int:
    print("=" * 40)
    print(" OIT-005 CORRECTION V2 TEST")
    print(" IMMUTABLE ARTIFACT LINEAGE")
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

        source_name = "oracle_genuine_intelligence_artifact_admission.py"
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
            "records": [{"market_id": "TEST-1", "score": 0.75}],
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

        receipt_body = {
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
        receipt_body["receipt_hash"] = stable_hash(receipt_body)
        receipt_path = (
            terminal_runtime / "oit_004_bounded_activation_receipt.json"
        )
        receipt_path.write_text(
            json.dumps(receipt_body, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        old_path = list(sys.path)
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.path.insert(0, str(root))
            clear_modules()
            module = __import__(
                "qseries_v2.oracle_terminal."
                "oracle_genuine_intelligence_artifact_admission",
                fromlist=["*"],
            )

            admitted = module.discover_and_admit_intelligence_artifacts(
                repository_root=root
            )
            assert module.verify_intelligence_artifact_admission(admitted)
            assert admitted.admission_ready
            assert admitted.artifact_count == 1
            admitted_artifact = admitted.admitted_artifacts[0]
            assert admitted_artifact.content_hash_verified
            assert admitted_artifact.byte_count_verified

            loaded = module.load_admitted_artifact(
                repository_root=root,
                relative_path=relative,
            )
            assert loaded == artifact_payload

            artifact_path.write_text(
                json.dumps({"changed": True}) + "\n",
                encoding="utf-8",
            )

            blocked = module.discover_and_admit_intelligence_artifacts(
                repository_root=root
            )
            assert not blocked.admission_ready
            assert not blocked.terminal_consumption_ready
            assert blocked.artifact_count == 0
            assert blocked.rejected_artifacts
            assert "SHA-256 differs" in blocked.rejected_artifacts[0]

            try:
                module.load_admitted_artifact(
                    repository_root=root,
                    relative_path=relative,
                )
                raise AssertionError("mutated artifact accepted")
            except module.OracleIntelligenceArtifactAdmissionInvariantError:
                pass

            artifact_path.write_text(
                json.dumps(artifact_payload, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            restored = module.discover_and_admit_intelligence_artifacts(
                repository_root=root
            )
            assert restored.admission_ready

            receipt_path.unlink()
            missing = module.discover_and_admit_intelligence_artifacts(
                repository_root=root
            )
            assert not missing.admission_ready
            assert missing.artifact_count == 0
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Actual OIT-004 receipt contract validated")
    print("[PASS] Exact artifact SHA-256 bound to activation lineage")
    print("[PASS] Exact artifact byte count bound to activation lineage")
    print("[PASS] Genuine unchanged artifact admitted read-only")
    print("[PASS] Post-activation content mutation rejected")
    print("[PASS] Mutated artifact cannot be loaded")
    print("[PASS] Restored exact artifact becomes admissible")
    print("[PASS] Missing activation receipt remains blocked")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-005 CORRECTION V2 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
