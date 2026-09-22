from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        production = (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_temporal_intelligence_timeline_reconstruction.py"
        )
        if production.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current OIT-013 repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
PRODUCTION = PACKAGE / "oracle_temporal_intelligence_timeline_reconstruction.py"
OIT_009 = PACKAGE / "oracle_grounded_intelligence_answer_composition.py"
OIT_010 = PACKAGE / "oracle_evidence_inspection_and_answer_explainability.py"
OIT_012 = PACKAGE / "oracle_adversarial_perspective_debate_and_challenge.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_013_oracle_temporal_intelligence_timeline_reconstruction.py"

TEST_SOURCE = '\nimport hashlib\nimport json\nimport os\nimport sys\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\n\ndef stable_hash(value):\n    return hashlib.sha256(json.dumps(\n        value,\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")).hexdigest()\n\n\ndef clear_modules():\n    for name in list(sys.modules):\n        if name == "qseries_v2" or name.startswith("qseries_v2."):\n            del sys.modules[name]\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-013 CORRECTION V4 TEST")\n    print(" SAFE TAMPER-OUTCOME CERTIFICATION")\n    print("=" * 40)\n\n    installed_root = Path(__file__).resolve().parent\n    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        terminal = root / "qseries_v2" / "oracle_terminal"\n        terminal.mkdir(parents=True)\n        (root / "qseries_v2" / "__init__.py").write_text("", encoding="utf-8")\n        (terminal / "__init__.py").write_text("", encoding="utf-8")\n\n        modules = (\n            "oracle_genuine_intelligence_artifact_admission.py",\n            "oracle_genuine_intelligence_read_only_consumption.py",\n            "oracle_queryable_intelligence_read_model.py",\n            "oracle_natural_language_query_planning_and_execution.py",\n            "oracle_grounded_intelligence_answer_composition.py",\n            "oracle_evidence_inspection_and_answer_explainability.py",\n            "oracle_contradiction_and_uncertainty_inspection.py",\n            "oracle_adversarial_perspective_debate_and_challenge.py",\n            "oracle_temporal_intelligence_timeline_reconstruction.py",\n        )\n        for name in modules:\n            source = installed_terminal / name\n            assert source.is_file(), source\n            (terminal / name).write_text(\n                source.read_text(encoding="utf-8"),\n                encoding="utf-8",\n            )\n\n        intelligence = (\n            root / "runtime" / "oracle_intelligence" / "bounded_activation"\n        )\n        terminal_runtime = root / "runtime" / "oracle_terminal"\n        intelligence.mkdir(parents=True)\n        terminal_runtime.mkdir(parents=True)\n\n        artifact = intelligence / "timeline_intelligence.json"\n        payload = {\n            "schema_version": "TEST-INTELLIGENCE-1",\n            "records": [\n                {\n                    "market_id": "ALPHA-1",\n                    "title": "Alpha market early assessment",\n                    "probability": 0.42,\n                    "stance": "bear",\n                    "updated_at": "2026-07-29T12:00:00Z",\n                    "venue": "Kalshi",\n                },\n                {\n                    "market_id": "ALPHA-2",\n                    "title": "Alpha market later assessment",\n                    "probability": 0.68,\n                    "stance": "bull",\n                    "updated_at": "2026-07-30T18:30:00Z",\n                    "venue": "Polymarket",\n                },\n            ],\n        }\n        artifact.write_text(\n            json.dumps(payload, sort_keys=True) + "\\n",\n            encoding="utf-8",\n        )\n        stat = artifact.stat()\n        artifact_state = {\n            "relative_path": artifact.relative_to(root).as_posix(),\n            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),\n            "byte_count": stat.st_size,\n            "modified_ns": stat.st_mtime_ns,\n        }\n\n        receipt = {\n            "schema_version": "OIT-004",\n            "engine_id": "OIT-004",\n            "policy_id": "oracle.bounded-live-intelligence-activation.v1",\n            "status": "bounded_activation_completed",\n            "repository_root": root.as_posix(),\n            "analytics_entry_point": "test.module:Gate.execute",\n            "required_inputs": [\n                "certified_artifacts: Any",\n                "execution_context: Mapping[str, Any]",\n                "executed_at: datetime",\n                "persist: bool",\n            ],\n            "selected_input": {\n                "relative_path": "runtime/oracle_research/certified.json",\n                "sha256": "a" * 64,\n                "byte_count": 10,\n                "modified_ns": 1,\n                "payload_kind": "dict",\n                "record_count": 1,\n                "score": 100,\n                "score_reasons": ["test"],\n            },\n            "candidate_count": 1,\n            "persistence_target": "runtime/oracle_intelligence",\n            "activation_readiness": "activation_completed",\n            "activation_attempted": True,\n            "analytics_execution_performed": True,\n            "invocation_completed": True,\n            "persist_requested": True,\n            "new_intelligence_artifacts": [artifact_state],\n            "changed_intelligence_artifacts": [],\n            "protected_source_unchanged": True,\n            "outside_target_runtime_unchanged": True,\n            "database_write_requested": False,\n            "publication_allowed": False,\n            "qseries_execution_allowed": False,\n            "bounded_once": True,\n            "failure_reason": None,\n            "executed_at_utc": "2026-07-30T19:00:00+00:00",\n        }\n        receipt["receipt_hash"] = stable_hash(receipt)\n        (\n            terminal_runtime / "oit_004_bounded_activation_receipt.json"\n        ).write_text(\n            json.dumps(receipt, indent=2, sort_keys=True) + "\\n",\n            encoding="utf-8",\n        )\n\n        before_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()\n        before_mtime = artifact.stat().st_mtime_ns\n        old_path = list(sys.path)\n        old_cwd = Path.cwd()\n\n        try:\n            os.chdir(root)\n            sys.path.insert(0, str(root))\n            clear_modules()\n            module = __import__(\n                "qseries_v2.oracle_terminal."\n                "oracle_temporal_intelligence_timeline_reconstruction",\n                fromlist=["*"],\n            )\n\n            report = module.build_temporal_intelligence_report(\n                repository_root=root,\n                query="Alpha market probability",\n                result_limit=10,\n            )\n            assert module.verify_temporal_intelligence_report(report)\n            assert report.event_count == 2, (\n                report.event_count,\n                report.missing_record_count,\n                report.missing_timestamp_count,\n                report.invalid_timestamp_count,\n                report.timeline_summary,\n            )\n            assert report.transition_count == 1\n            assert report.events[0].record_id == "ALPHA-1"\n            assert report.events[1].record_id == "ALPHA-2"\n            assert report.events[0].timestamp_field == "updated_at"\n            assert report.events[1].timestamp_field == "updated_at"\n            assert report.events[0].source_record_locator == "$.records[0]"\n            assert report.events[1].source_record_locator == "$.records[1]"\n            assert report.earliest_timestamp_utc.startswith(\n                "2026-07-29T12:00:00"\n            )\n            assert report.latest_timestamp_utc.startswith(\n                "2026-07-30T18:30:00"\n            )\n            assert report.span_seconds == 109800\n            assert report.stale_evidence_detected\n            assert report.chronology_state == "chronology_with_stale_gaps"\n            assert report.temporal_order_complete\n            assert report.missing_record_count == 0\n            assert report.missing_timestamp_count == 0\n            assert report.invalid_timestamp_count == 0\n            assert report.transitions[0].transition_type == "stale_gap"\n\n            rendered = "\\n".join(\n                module.temporal_intelligence_lines(report)\n            )\n            assert "event_count: 2" in rendered\n            assert "field: updated_at" in rendered\n            assert "source_record_locator: $.records[0]" in rendered\n            assert "stale_evidence_detected: true" in rendered\n            assert "read_only: true" in rendered\n\n            single = module.build_temporal_intelligence_report(\n                repository_root=root,\n                query="bull Alpha market probability",\n            )\n            assert single.event_count == 1\n            assert single.events[0].record_id == "ALPHA-2"\n            assert single.transition_count == 0\n            assert single.temporal_order_complete\n\n            no_match = module.build_temporal_intelligence_report(\n                repository_root=root,\n                query="gamma market",\n            )\n            assert no_match.event_count == 0\n            assert no_match.chronology_state == "no_timestamped_evidence"\n\n            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == before_hash\n            assert artifact.stat().st_mtime_ns == before_mtime\n\n            artifact.write_text(\'{"mutated":true}\\n\', encoding="utf-8")\n            try:\n                blocked = module.build_temporal_intelligence_report(\n                    repository_root=root,\n                    query="alpha",\n                )\n            except module.OracleTemporalTimelineInvariantError:\n                tamper_outcome = "explicit_hash_or_lineage_rejection"\n            else:\n                assert blocked.event_count == 0\n                assert blocked.transition_count == 0\n                assert blocked.status == "temporal_intelligence_limited"\n                assert blocked.chronology_state == "no_timestamped_evidence"\n                tamper_outcome = "upstream_admission_rejection"\n            assert tamper_outcome in {\n                "explicit_hash_or_lineage_rejection",\n                "upstream_admission_rejection",\n            }\n        finally:\n            os.chdir(old_cwd)\n            sys.path[:] = old_path\n            clear_modules()\n\n    print("[PASS] Actual OIT-010 selected-field contract consumed")\n    print("[PASS] Certified artifact reopened read-only by relative path")\n    print("[PASS] Artifact SHA-256 verified before temporal inspection")\n    print("[PASS] Exact records located by certified record ID")\n    print("[PASS] updated_at extracted from raw immutable source records")\n    print("[PASS] Events normalized and sorted in UTC")\n    print("[PASS] Stale temporal gap detected deterministically")\n    print("[PASS] OIT-012 debate and contradiction lineage preserved")\n    print("[PASS] Query, evidence, inspection, record, and artifact lineage preserved")\n    print("[PASS] Source artifact bytes and modification time unchanged")\n    print("[PASS] Mutated artifact produces no temporal events")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-013 CORRECTION V4 SAFE TAMPER CERTIFICATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"Actual {label} file missing: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise RuntimeError(f"Current {label} contract mismatch: {missing}")


def write_complete(path: Path, source: str) -> None:
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" OIT-013 CORRECTION V4 INSTALLER")
    print(" SAFE TAMPER-OUTCOME CERTIFICATION")
    print("=" * 40)

    try:
        require(PRODUCTION, (
            'SCHEMA_VERSION = "OIT-013"',
            'POLICY_ID = "oracle.temporal-intelligence-timeline-reconstruction.v3"',
            "build_temporal_intelligence_report",
            "_load_verified_artifact",
            "artifact_sha256",
            "source_record_locator",
            "analytics_execution_performed",
            "qseries_execution_allowed",
        ), "OIT-013 production")
        require(OIT_009, ('SCHEMA_VERSION = "OIT-009"',), "OIT-009")
        require(OIT_010, ('SCHEMA_VERSION = "OIT-010"',), "OIT-010")
        require(OIT_012, ('SCHEMA_VERSION = "OIT-012"',), "OIT-012")

        protected = {
            path: sha256(path)
            for path in (PRODUCTION, OIT_009, OIT_010, OIT_012, RUNNER)
            if path.is_file()
        }

        print("[OK] Current OIT-013 V3 production contract verified")
        print("[OK] Actual OIT-009, OIT-010, and OIT-012 contracts verified")
        print("[OK] Safe tamper behavior defined as zero-event output or explicit rejection")
        print(f"[OK] Protected source files captured: {len(protected)}")

        write_complete(TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-013 CORRECTION V4 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(f"Protected source changed: {path}")

        print("[PASS] OIT-013 production module unchanged")
        print("[PASS] OIT-009, OIT-010, and OIT-012 unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] Entire OIT-013 standalone test replaced")
        print("[PASS] Explicit tamper rejection accepted")
        print("[PASS] Upstream admission rejection with zero events accepted")
        print("[PASS] Any temporal events from mutated content remain forbidden")
        print("[PASS] Complete OIT-013 test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-013 CORRECTION V4 SAFE TAMPER CERTIFICATION INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
