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
        if (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_natural_language_query_planning_and_execution.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository containing OIT-008.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_007 = PACKAGE / "oracle_queryable_intelligence_read_model.py"
PRODUCTION = PACKAGE / "oracle_natural_language_query_planning_and_execution.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_008_oracle_natural_language_query_planning_and_execution.py"

OLD_EXECUTION = """    if model.query_ready:
        broad_matches = search_queryable_records(
            model,
            query=" ".join(plan.search_terms),
        )
        candidates = broad_matches if broad_matches else model.records
        for record in candidates:
            matched_terms = _matched_terms(
                record,
                plan.search_terms,
            )
            matched_hints = _field_hint_matches(
                record,
                plan.field_hints,
            )
            if not matched_terms:
                continue
            score = _score_record(
                record,
                matched_terms=matched_terms,
                matched_hints=matched_hints,
            )
            matches.append(
                (record, matched_terms, matched_hints, score)
            )
"""

NEW_EXECUTION = """    if model.query_ready:
        required_terms = _required_identity_terms(plan.search_terms)
        broad_matches = search_queryable_records(
            model,
            query=" ".join(plan.search_terms),
        )
        candidates = broad_matches if broad_matches else model.records
        for record in candidates:
            matched_terms = _matched_terms(
                record,
                plan.search_terms,
            )
            matched_hints = _field_hint_matches(
                record,
                plan.field_hints,
            )
            if required_terms and not all(
                term in matched_terms for term in required_terms
            ):
                continue
            if not required_terms and not matched_terms:
                continue
            score = _score_record(
                record,
                matched_terms=matched_terms,
                matched_hints=matched_hints,
            )
            matches.append(
                (record, matched_terms, matched_hints, score)
            )
"""

OLD_TEST = """            no_match = module.execute_natural_language_query(
                repository_root=root,
                query="gamma market",
            )
            assert no_match.query_ready
            assert no_match.match_count == 0
            assert "no matching" in no_match.failure_reason
"""

NEW_TEST = """            no_match = module.execute_natural_language_query(
                repository_root=root,
                query="gamma market",
            )
            assert no_match.query_ready
            assert no_match.match_count == 0
            assert "no matching" in no_match.failure_reason

            generic_match = module.execute_natural_language_query(
                repository_root=root,
                query="bull market probability",
            )
            assert generic_match.query_ready
            assert generic_match.match_count == 2
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_sources() -> dict[Path, str]:
    result = {}
    prefixes = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in prefixes:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    result[path] = sha256(path)
    for path in (OIT_007, RUNNER):
        if path.is_file():
            result[path] = sha256(path)
    return result


def write_complete(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" OIT-008 CORRECTION V2 INSTALLER")
    print(" DISTINCTIVE QUERY TERM ENFORCEMENT")
    print("=" * 40)
    try:
        if not OIT_007.is_file():
            raise RuntimeError(f"Actual OIT-007 module missing: {OIT_007}")
        if not PRODUCTION.is_file():
            raise RuntimeError(f"Actual OIT-008 module missing: {PRODUCTION}")
        if not TEST.is_file():
            raise RuntimeError(f"Actual OIT-008 test missing: {TEST}")
        if not RUNNER.is_file():
            raise RuntimeError(f"Actual OIT-008 runner missing: {RUNNER}")

        production = PRODUCTION.read_text(encoding="utf-8")
        test = TEST.read_text(encoding="utf-8")

        required = (
            'SCHEMA_VERSION = "OIT-008"',
            "FIELD_ALIASES = {",
            "execute_natural_language_query",
            OLD_EXECUTION,
        )
        missing = [item for item in required if item not in production]
        if missing:
            raise RuntimeError(
                f"Actual OIT-008 source differs from expected contract: {missing[:3]}"
            )
        if OLD_TEST not in test:
            raise RuntimeError("Actual OIT-008 test differs from expected contract")

        protected = protected_sources()
        print("[OK] Actual OIT-007 queryable read model verified")
        print("[OK] Actual OIT-008 natural-language query contract verified")
        print("[OK] Generic-term false-positive defect isolated")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        alias_anchor = "}\n\n\nclass OracleNaturalLanguageQueryInvariantError"
        production = production.replace(
            alias_anchor,
            "}\n\nGENERIC_QUERY_TERMS = frozenset(FIELD_ALIASES)\n\n\n"
            "class OracleNaturalLanguageQueryInvariantError",
            1,
        )

        function_anchor = "\ndef _field_hints(terms: tuple[str, ...])"
        required_function = """
def _required_identity_terms(
    terms: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        term for term in terms
        if term not in GENERIC_QUERY_TERMS
    )

"""
        production = production.replace(
            function_anchor,
            "\n" + required_function
            + "def _field_hints(terms: tuple[str, ...])",
            1,
        )
        production = production.replace(OLD_EXECUTION, NEW_EXECUTION, 1)
        test = test.replace(OLD_TEST, NEW_TEST, 1)

        write_complete(PRODUCTION, production)
        write_complete(TEST, test)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-008 CORRECTION V2 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(f"Protected production source changed: {path}")

        print("[PASS] OIT-007 production module unchanged")
        print("[PASS] OIT-008 terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Distinctive non-generic query terms now mandatory")
        print("[PASS] Generic field-only queries remain supported")
        print("[PASS] gamma market false positive rejected")
        print("[PASS] Complete OIT-008 production test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-008 CORRECTION V2 INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
