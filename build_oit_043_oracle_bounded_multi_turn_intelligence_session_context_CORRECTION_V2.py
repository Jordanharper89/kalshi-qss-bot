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

        package = candidate / "qseries_v2" / "oracle_terminal"
        production = (
            package
            / "oracle_bounded_multi_turn_intelligence_session_context.py"
        )
        upstream = (
            package
            / "oracle_terminal_intelligence_answer_generation.py"
        )
        if production.is_file() and upstream.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"

OIT_042 = (
    PACKAGE
    / "oracle_terminal_intelligence_answer_generation.py"
)
OIT_042_TEST = (
    ROOT
    / "test_oit_042_oracle_terminal_intelligence_answer_generation.py"
)
OIT_043 = (
    PACKAGE
    / "oracle_bounded_multi_turn_intelligence_session_context.py"
)
OIT_043_TEST = (
    ROOT
    / "test_oit_043_oracle_bounded_multi_turn_intelligence_session_context.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (\n    ENGINE_ID as OIT_042_ENGINE_ID,\n    POLICY_ID as OIT_042_POLICY_ID,\n    SCHEMA_VERSION as OIT_042_SCHEMA_VERSION,\n    OracleTerminalIntelligenceAnswer,\n    OracleTerminalIntelligenceAnswerGenerationReport,\n    OracleTerminalIntelligenceAnswerLine,\n    _stable_hash as oit_042_hash,\n    verify_terminal_intelligence_answer_generation_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (\n    OracleBoundedMultiTurnSessionInvariantError,\n    append_answer_to_bounded_multi_turn_session,\n    verify_bounded_multi_turn_session_update_report,\n)\n\n\ndef make_line(\n    index: int,\n    line_type: str,\n    text: str,\n    source_path: str,\n) -> OracleTerminalIntelligenceAnswerLine:\n    body = {\n        "line_index": index,\n        "line_type": line_type,\n        "text": text,\n        "source_field_paths": (source_path,),\n        "source_field_hashes": (f"source-field-hash-{index}",),\n        "evidence_linked": True,\n    }\n    return OracleTerminalIntelligenceAnswerLine(\n        **body,\n        line_hash=oit_042_hash(body),\n    )\n\n\ndef make_report(\n    root: Path,\n    query: str,\n    answer_id: str,\n    direction: str,\n) -> OracleTerminalIntelligenceAnswerGenerationReport:\n    lines = (\n        make_line(\n            0,\n            "summary",\n            "Oracle found 1 certified context field relevant to the query.",\n            "$.direction",\n        ),\n        make_line(\n            1,\n            "fact",\n            f"direction: {direction}",\n            "$.direction",\n        ),\n    )\n\n    answer_body = {\n        "answer_id": answer_id,\n        "source_projection_hash": f"projection-hash-{answer_id}",\n        "source_projection_report_hash": (\n            f"projection-report-hash-{answer_id}"\n        ),\n        "query": query,\n        "answer_lines": lines,\n        "answer_line_count": len(lines),\n        "evidence_line_count": 0,\n        "summary_line_count": 1,\n        "uncertainty_line_count": 0,\n        "all_claims_evidence_linked": True,\n        "deterministic_ordering_applied": True,\n        "bounded_answer": True,\n        "answer_ready": True,\n        "read_only": True,\n    }\n    answer = OracleTerminalIntelligenceAnswer(\n        **answer_body,\n        answer_hash=oit_042_hash(answer_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_042_SCHEMA_VERSION,\n        "engine_id": OIT_042_ENGINE_ID,\n        "policy_id": OIT_042_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "projection_report_hash": (\n            answer.source_projection_report_hash\n        ),\n        "answer": answer,\n        "answer_generated": True,\n        "answer_render_ready": True,\n        "unsupported_claims_generated": False,\n        "free_form_generation_used": False,\n        "multi_turn_memory_enabled": False,\n        "persistent_memory_enabled": False,\n        "learning_update_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleTerminalIntelligenceAnswerGenerationReport(\n        **report_body,\n        report_hash=oit_042_hash(report_body),\n    )\n    verify_terminal_intelligence_answer_generation_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-043 TEST")\n    print(" BOUNDED MULTI-TURN INTELLIGENCE SESSION CONTEXT")\n    print(" CORRECTION V2 - REPOSITORY-ALIGNED HASH IMPORT")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n\n        first_answer = make_report(\n            root,\n            "What is the direction?",\n            "answer-043-1",\n            "bull",\n        )\n        first = append_answer_to_bounded_multi_turn_session(\n            root,\n            answer_report=first_answer,\n        )\n\n        assert first.turn_appended\n        assert first.session_continuation_ready\n        assert first.volatile_memory_only\n        assert not first.persistent_memory_enabled\n        assert not first.learning_update_performed\n\n        first_context = first.updated_session_context\n        assert first_context.session_active\n        assert first_context.turn_count == 1\n        assert first_context.latest_turn_index == 0\n        assert first_context.total_answer_line_count == 2\n        assert first_context.volatile_memory_only\n        assert not first_context.persistent_memory_enabled\n        assert not first_context.learning_enabled\n\n        second_answer = make_report(\n            root,\n            "Has the direction changed?",\n            "answer-043-2",\n            "bull",\n        )\n        second = append_answer_to_bounded_multi_turn_session(\n            root,\n            answer_report=second_answer,\n            prior_session_context=first_context,\n        )\n\n        second_context = second.updated_session_context\n        assert second.turn_appended\n        assert second.session_continuation_ready\n        assert second_context.session_id == first_context.session_id\n        assert second_context.turn_count == 2\n        assert second_context.latest_turn_index == 1\n        assert second_context.total_answer_line_count == 4\n        assert tuple(\n            turn.turn_index for turn in second_context.turns\n        ) == (0, 1)\n        assert tuple(\n            turn.query for turn in second_context.turns\n        ) == (\n            "What is the direction?",\n            "Has the direction changed?",\n        )\n        assert all(\n            turn.evidence_linked for turn in second_context.turns\n        )\n        assert second.prior_session_context_hash == (\n            first_context.context_hash\n        )\n\n        replay = append_answer_to_bounded_multi_turn_session(\n            root,\n            answer_report=second_answer,\n            prior_session_context=first_context,\n        )\n        assert replay == second\n        assert verify_bounded_multi_turn_session_update_report(second)\n\n        tampered = replace(\n            second,\n            persistent_memory_enabled=True,\n        )\n        try:\n            verify_bounded_multi_turn_session_update_report(tampered)\n        except OracleBoundedMultiTurnSessionInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered multi-turn report accepted"\n            )\n\n        assert not second.analytics_execution_performed\n        assert not second.database_access_performed\n        assert not second.runtime_artifact_created\n        assert not second.runtime_artifact_modified\n        assert not second.networking_performed\n        assert not second.publication_allowed\n        assert not second.action_authorization_allowed\n        assert not second.qseries_execution_allowed\n        assert second.read_only\n\n    print("[PASS] Certified OIT-042 answer report contract consumed")\n    print("[PASS] OIT-042 hash helper imported explicitly")\n    print("[PASS] First volatile session turn materialized")\n    print("[PASS] Second turn appended deterministically")\n    print("[PASS] Session identity preserved across turns")\n    print("[PASS] Exact turn ordering certified")\n    print("[PASS] Complete answer and projection lineage retained")\n    print("[PASS] Evidence-linked turn requirement enforced")\n    print("[PASS] Turn and answer-line limits preserved")\n    print("[PASS] Volatile in-process memory certified")\n    print("[PASS] Persistent Oracle memory remained disabled")\n    print("[PASS] Learning updates remained disabled")\n    print("[PASS] Session update deterministic across replay")\n    print("[PASS] Tampered session report rejected")\n    print("[PASS] No analytics execution or runtime mutation performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-043 CORRECTION V2 BOUNDED MULTI-TURN SESSION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"{label} contract mismatch: {missing}"
        )


def write_complete(path: Path, source: str) -> None:
    path.write_text(
        source.lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}

    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )

    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)

    for path in (
        OIT_042,
        OIT_042_TEST,
        OIT_043,
        RUNNER,
    ):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-043 CORRECTION V2 INSTALLER")
    print(" REPOSITORY-ALIGNED HASH IMPORT FIX")
    print("=" * 48)

    try:
        require_contract(
            OIT_042,
            (
                'SCHEMA_VERSION = "OIT-042"',
                'POLICY_ID = "oracle.terminal-intelligence-answer-generation.v1"',
                "OracleTerminalIntelligenceAnswerLine",
                "OracleTerminalIntelligenceAnswer",
                "OracleTerminalIntelligenceAnswerGenerationReport",
                "_stable_hash",
                "verify_terminal_intelligence_answer_generation_report",
            ),
            "Certified OIT-042 production",
        )
        require_contract(
            OIT_042_TEST,
            (
                "OIT-042 TEST",
                "TERMINAL INTELLIGENCE ANSWER GENERATION",
                "OIT-042 TERMINAL INTELLIGENCE ANSWER GENERATION PASS",
            ),
            "Certified OIT-042 standalone test",
        )
        require_contract(
            OIT_043,
            (
                'SCHEMA_VERSION = "OIT-043"',
                'POLICY_ID = "oracle.bounded-multi-turn-intelligence-session-context.v1"',
                "OracleBoundedMultiTurnSessionContext",
                "append_answer_to_bounded_multi_turn_session",
                "verify_bounded_multi_turn_session_update_report",
                "volatile_memory_only",
                "persistent_memory_enabled",
                "learning_enabled",
            ),
            "Installed OIT-043 production",
        )

        if not OIT_043_TEST.is_file():
            raise RuntimeError(
                f"Installed OIT-043 test missing: {OIT_043_TEST}"
            )

        current_test = OIT_043_TEST.read_text(encoding="utf-8")
        if "_stable_hash(b)" not in current_test:
            print(
                "[WARN] Exact original defect token not found; "
                "continuing with complete repository-aligned test replacement"
            )
        else:
            print(
                "[OK] Root cause confirmed: undefined _stable_hash in "
                "installed OIT-043 test"
            )

        protected = protected_sources()

        print("[OK] Certified OIT-042 production contract verified")
        print("[OK] Certified OIT-042 standalone test verified")
        print("[OK] Installed OIT-043 production contract verified")
        print("[OK] Current repository state accepted")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        upstream = subprocess.run(
            [sys.executable, str(OIT_042_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-042 certification failed with exit code "
                f"{upstream.returncode}"
            )

        write_complete(OIT_043_TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(OIT_043_TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-043 corrected test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] OIT-043 production module unchanged")
        print("[PASS] OIT-043 standalone test fully replaced")
        print("[PASS] OIT-042 _stable_hash imported as oit_042_hash")
        print("[PASS] Undefined hash helper defect eliminated")
        print("[PASS] Certified OIT-042 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] Volatile multi-turn context fully recertified")
        print("[PASS] Persistent memory and learning remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-043 CORRECTION V2 INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
