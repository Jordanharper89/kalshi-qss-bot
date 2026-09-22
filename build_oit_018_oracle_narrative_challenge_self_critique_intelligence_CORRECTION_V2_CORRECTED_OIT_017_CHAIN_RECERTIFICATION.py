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
        required = (
            candidate
            / "qseries_v2"
            / "oracle_terminal"
            / "oracle_cross_market_narrative_evolution_intelligence.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_017 = (
    PACKAGE
    / "oracle_cross_market_narrative_evolution_intelligence.py"
)
OIT_017_TEST = (
    ROOT
    / "test_oit_017_oracle_cross_market_narrative_evolution_intelligence.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_narrative_challenge_self_critique_intelligence.py"
)
TEST = (
    ROOT
    / "test_oit_018_oracle_narrative_challenge_self_critique_intelligence.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (\n    ENGINE_ID as OIT_017_ENGINE_ID,\n    POLICY_ID as OIT_017_POLICY_ID,\n    SCHEMA_VERSION as OIT_017_SCHEMA_VERSION,\n    OracleNarrativeEvolutionFinding,\n    OracleNarrativeEvolutionReport,\n    _stable_hash as oit_017_hash,\n    verify_narrative_evolution_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_narrative_challenge_self_critique_intelligence import (\n    OracleNarrativeChallengeInvariantError,\n    build_narrative_challenge_report,\n    verify_narrative_challenge_report,\n)\n\n\ndef make_narrative(\n    index: int,\n    cause: str,\n    effect: str,\n    *,\n    state: str,\n    strength: float,\n    stability: float,\n    reversal: float,\n    contradiction: float,\n    uncertainty: float,\n    support: float,\n    monitoring: bool,\n):\n    body = {\n        "finding_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "source_finding_hash": f"uncertainty-{index}",\n        "narrative_state": state,\n        "narrative_direction": (\n            "support_accumulating"\n            if state == "strengthening"\n            else "opposing_evidence_dominant"\n        ),\n        "narrative_strength": strength,\n        "narrative_stability": stability,\n        "reversal_risk": reversal,\n        "contradiction_pressure": contradiction,\n        "uncertainty_pressure": uncertainty,\n        "evidence_support": support,\n        "requires_monitoring": monitoring,\n        "evolution_signals": ("certified narrative signal",),\n        "rationale": ("certified narrative rationale",),\n        "read_only": True,\n    }\n    return OracleNarrativeEvolutionFinding(\n        **body,\n        finding_hash=oit_017_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        make_narrative(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            state="strengthening",\n            strength=0.82,\n            stability=0.80,\n            reversal=0.15,\n            contradiction=0.05,\n            uncertainty=0.20,\n            support=0.86,\n            monitoring=False,\n        ),\n        make_narrative(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            state="reversing",\n            strength=0.78,\n            stability=0.22,\n            reversal=0.84,\n            contradiction=0.82,\n            uncertainty=0.72,\n            support=0.30,\n            monitoring=True,\n        ),\n    )\n    body = {\n        "schema_version": OIT_017_SCHEMA_VERSION,\n        "engine_id": OIT_017_ENGINE_ID,\n        "policy_id": OIT_017_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Challenge the current Bitcoin narratives.",\n        "uncertainty_report_hash": "uncertainty-report-hash",\n        "findings": findings,\n        "finding_count": len(findings),\n        "strengthening_count": sum(\n            item.narrative_state == "strengthening" for item in findings\n        ),\n        "weakening_count": sum(\n            item.narrative_state == "weakening" for item in findings\n        ),\n        "fragmented_count": sum(\n            item.narrative_state == "fragmented" for item in findings\n        ),\n        "reversing_count": sum(\n            item.narrative_state == "reversing" for item in findings\n        ),\n        "stable_count": sum(\n            item.narrative_state == "stable" for item in findings\n        ),\n        "monitoring_required_count": sum(\n            item.requires_monitoring for item in findings\n        ),\n        "narrative_state": "narrative_reversal_detected",\n        "narrative_summary": "One strengthening and one reversing narrative.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleNarrativeEvolutionReport(\n        **body,\n        report_hash=oit_017_hash(body),\n    )\n    verify_narrative_evolution_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-018 CORRECTION V2 TEST")\n    print(" NARRATIVE CHALLENGE AND SELF-CRITIQUE")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n\n        assert source.finding_count == 2\n        assert source.strengthening_count == 1\n        assert source.reversing_count == 1\n        assert source.monitoring_required_count == 1\n\n        report = build_narrative_challenge_report(\n            root,\n            source.query,\n            narrative_report=source,\n        )\n\n        assert report.narrative_report_hash == source.report_hash\n        assert report.finding_count == 2\n        assert report.passed_count == 1\n        assert report.failed_count == 1\n        assert report.fragile_count == 1\n        assert report.monitoring_required_count == 1\n\n        passed, failed = report.findings\n        assert passed.challenge_state == "passed"\n        assert passed.challenge_passed\n        assert passed.surviving_confidence >= 0.50\n\n        assert failed.challenge_state == "failed"\n        assert not failed.challenge_passed\n        assert failed.fragility_score >= 0.70\n        assert failed.counter_evidence_pressure > (\n            passed.counter_evidence_pressure\n        )\n\n        assert passed.source_narrative_hash == (\n            source.findings[0].finding_hash\n        )\n        assert failed.source_narrative_hash == (\n            source.findings[1].finding_hash\n        )\n\n        assert all(item.fragile_assumptions for item in report.findings)\n        assert all(item.counter_arguments for item in report.findings)\n        assert all(item.falsification_tests for item in report.findings)\n\n        replay = build_narrative_challenge_report(\n            root,\n            source.query,\n            narrative_report=source,\n        )\n        assert replay == report\n        assert verify_narrative_challenge_report(report)\n\n        tampered = replace(\n            report,\n            challenge_summary=report.challenge_summary + " tampered",\n        )\n        try:\n            verify_narrative_challenge_report(tampered)\n        except OracleNarrativeChallengeInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered challenge report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Corrected certified OIT-017 narrative report consumed")\n    print("[PASS] OIT-017 fixture counts derived from narrative findings")\n    print("[PASS] Strong narrative survived bounded challenge")\n    print("[PASS] Fragile narrative failed bounded challenge")\n    print("[PASS] Counter-evidence pressure quantified")\n    print("[PASS] Fragile assumptions surfaced")\n    print("[PASS] Counter-arguments generated")\n    print("[PASS] Falsification tests generated")\n    print("[PASS] Complete corrected OIT-017 lineage retained")\n    print("[PASS] Challenge report deterministic across replay")\n    print("[PASS] Tampered challenge report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-018 CORRECTION V2 SELF-CRITIQUE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], name: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{name} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{name} contract mismatch: {missing}")


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
    for path in (OIT_017, OIT_017_TEST, PRODUCTION, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 40)
    print(" OIT-018 CORRECTION V2 INSTALLER")
    print(" CORRECTED OIT-017 CHAIN RECERTIFICATION")
    print("=" * 40)
    try:
        require_contract(
            OIT_017,
            (
                'SCHEMA_VERSION = "OIT-017"',
                (
                    'POLICY_ID = '
                    '"oracle.cross-market-narrative-evolution-intelligence.v1"'
                ),
                "OracleNarrativeEvolutionReport",
                "OracleNarrativeEvolutionFinding",
                "build_narrative_evolution_report",
                "verify_narrative_evolution_report",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-017 production",
        )
        require_contract(
            OIT_017_TEST,
            (
                "OIT-017 CORRECTION V2 TEST",
                "Fixture unresolved-evidence count derived from findings",
                "Both evidence-requiring findings counted exactly",
                "OIT-017 CORRECTION V2 NARRATIVE EVOLUTION PASS",
            ),
            "Corrected OIT-017 standalone test",
        )
        require_contract(
            PRODUCTION,
            (
                'SCHEMA_VERSION = "OIT-018"',
                (
                    'POLICY_ID = '
                    '"oracle.narrative-challenge-self-critique-intelligence.v1"'
                ),
                "OracleNarrativeChallengeReport",
                "OracleNarrativeChallengeFinding",
                "build_narrative_challenge_report",
                "verify_narrative_challenge_report",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Current OIT-018 production",
        )

        protected = protected_sources()
        production_hash = sha256(PRODUCTION)
        oit_017_hash = sha256(OIT_017)
        oit_017_test_hash = sha256(OIT_017_TEST)

        print("[OK] Corrected OIT-017 production contract verified")
        print("[OK] OIT-017 Correction V2 standalone test verified")
        print("[OK] Current OIT-018 production contract verified")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_narrative_challenge_self_critique_intelligence "
            "import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(
                current + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        upstream = subprocess.run(
            [sys.executable, str(OIT_017_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"Corrected OIT-017 certification failed with exit code "
                f"{upstream.returncode}"
            )

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-018 Correction V2 test failed with exit code "
                f"{completed.returncode}"
            )

        if sha256(OIT_017) != oit_017_hash:
            raise RuntimeError("OIT-017 production module changed unexpectedly")
        if sha256(OIT_017_TEST) != oit_017_test_hash:
            raise RuntimeError("OIT-017 corrected test changed unexpectedly")
        if sha256(PRODUCTION) != production_hash:
            raise RuntimeError("OIT-018 production module changed unexpectedly")

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Corrected OIT-017 production module unchanged")
        print("[PASS] OIT-017 Correction V2 test unchanged")
        print("[PASS] OIT-018 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Entire OIT-018 standalone test replaced")
        print("[PASS] Corrected OIT-017 chain certified before OIT-018")
        print("[PASS] OIT-018 challenge and self-critique test passed")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OIT-018 CORRECTION V2 CORRECTED "
            "CHAIN RECERTIFICATION INSTALLED"
        )
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
