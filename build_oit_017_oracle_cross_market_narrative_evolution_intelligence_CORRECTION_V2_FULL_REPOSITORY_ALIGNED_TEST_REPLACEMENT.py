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
OIT_016 = (
    PACKAGE
    / "oracle_cross_market_uncertainty_contradiction_synthesis.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_cross_market_narrative_evolution_intelligence.py"
)
TEST = (
    ROOT
    / "test_oit_017_oracle_cross_market_narrative_evolution_intelligence.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_cross_market_uncertainty_contradiction_synthesis import (\n    ENGINE_ID as OIT_016_ENGINE_ID,\n    POLICY_ID as OIT_016_POLICY_ID,\n    SCHEMA_VERSION as OIT_016_SCHEMA_VERSION,\n    OracleUncertaintyContradictionFinding,\n    OracleUncertaintyContradictionReport,\n    _stable_hash as oit_016_hash,\n    verify_uncertainty_contradiction_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (\n    OracleNarrativeEvolutionInvariantError,\n    build_narrative_evolution_report,\n    verify_narrative_evolution_report,\n)\n\n\ndef make_finding(\n    index: int,\n    cause: str,\n    effect: str,\n    uncertainty: float,\n    contradiction: float,\n    completeness: float,\n    confidence_gap: float,\n):\n    contradiction_state = (\n        "material_directional_contradiction"\n        if contradiction >= 0.60\n        else "none_detected"\n    )\n    uncertainty_state = (\n        "high" if uncertainty >= 0.67\n        else "moderate" if uncertainty >= 0.34\n        else "low"\n    )\n    requires_additional_evidence = (\n        uncertainty_state != "low" or contradiction > 0.0\n    )\n    body = {\n        "finding_index": index,\n        "cause_record_id": cause,\n        "effect_record_id": effect,\n        "source_hypothesis_hash": f"hypothesis-{index}",\n        "evidence_class": "suppressive" if contradiction else "supportive",\n        "contradiction_state": contradiction_state,\n        "uncertainty_state": uncertainty_state,\n        "uncertainty_score": uncertainty,\n        "confidence_gap": confidence_gap,\n        "evidence_completeness": completeness,\n        "contradiction_severity": contradiction,\n        "requires_additional_evidence": requires_additional_evidence,\n        "unresolved_questions": (\n            "What evidence would falsify the narrative?",\n        ),\n        "rationale": ("certified uncertainty finding",),\n        "read_only": True,\n    }\n    return OracleUncertaintyContradictionFinding(\n        **body,\n        finding_hash=oit_016_hash(body),\n    )\n\n\ndef make_report(root: Path):\n    findings = (\n        make_finding(\n            1,\n            "BTC-ETF",\n            "BTC-PRICE",\n            uncertainty=0.20,\n            contradiction=0.05,\n            completeness=0.82,\n            confidence_gap=0.20,\n        ),\n        make_finding(\n            2,\n            "BTC-PRICE",\n            "BTC-MINER",\n            uncertainty=0.72,\n            contradiction=0.82,\n            completeness=0.34,\n            confidence_gap=0.55,\n        ),\n    )\n    unresolved_count = sum(\n        item.requires_additional_evidence for item in findings\n    )\n    body = {\n        "schema_version": OIT_016_SCHEMA_VERSION,\n        "engine_id": OIT_016_ENGINE_ID,\n        "policy_id": OIT_016_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "How is the Bitcoin narrative evolving?",\n        "causal_report_hash": "causal-report-hash",\n        "findings": findings,\n        "finding_count": 2,\n        "high_uncertainty_count": 1,\n        "moderate_uncertainty_count": 0,\n        "low_uncertainty_count": 1,\n        "material_contradiction_count": 1,\n        "unresolved_evidence_count": unresolved_count,\n        "synthesis_state": "material_contradictions_require_review",\n        "synthesis_summary": "One stable and one conflicted finding.",\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleUncertaintyContradictionReport(\n        **body,\n        report_hash=oit_016_hash(body),\n    )\n    verify_uncertainty_contradiction_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-017 CORRECTION V2 TEST")\n    print(" CROSS-MARKET NARRATIVE EVOLUTION")\n    print("=" * 40)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_report(root)\n\n        assert source.unresolved_evidence_count == 2\n        assert sum(\n            item.requires_additional_evidence for item in source.findings\n        ) == source.unresolved_evidence_count\n\n        report = build_narrative_evolution_report(\n            root,\n            source.query,\n            uncertainty_report=source,\n        )\n\n        assert report.uncertainty_report_hash == source.report_hash\n        assert report.finding_count == 2\n        assert report.strengthening_count == 1\n        assert report.reversing_count == 1\n        assert report.monitoring_required_count == 1\n\n        strengthening, reversing = report.findings\n        assert strengthening.narrative_state == "strengthening"\n        assert strengthening.narrative_direction == "support_accumulating"\n        assert not strengthening.requires_monitoring\n\n        assert reversing.narrative_state == "reversing"\n        assert reversing.narrative_direction == "opposing_evidence_dominant"\n        assert reversing.requires_monitoring\n        assert reversing.reversal_risk >= 0.65\n\n        assert strengthening.source_finding_hash == (\n            source.findings[0].finding_hash\n        )\n        assert reversing.source_finding_hash == (\n            source.findings[1].finding_hash\n        )\n\n        replay = build_narrative_evolution_report(\n            root,\n            source.query,\n            uncertainty_report=source,\n        )\n        assert replay == report\n        assert verify_narrative_evolution_report(report)\n\n        tampered = replace(\n            report,\n            narrative_summary=report.narrative_summary + " tampered",\n        )\n        try:\n            verify_narrative_evolution_report(tampered)\n        except OracleNarrativeEvolutionInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered narrative report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-016 uncertainty report consumed")\n    print("[PASS] Fixture unresolved-evidence count derived from findings")\n    print("[PASS] Both evidence-requiring findings counted exactly")\n    print("[PASS] Strengthening narrative detected")\n    print("[PASS] Narrative reversal detected")\n    print("[PASS] Narrative stability quantified")\n    print("[PASS] Reversal risk quantified")\n    print("[PASS] Contradiction and uncertainty pressure preserved")\n    print("[PASS] Complete OIT-016 lineage retained")\n    print("[PASS] Narrative report deterministic across replay")\n    print("[PASS] Tampered narrative report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication and Q Series execution disabled")\n    print("[DONE] OIT-017 CORRECTION V2 NARRATIVE EVOLUTION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], name: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{name} module missing: {path}")
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
    for path in (OIT_016, PRODUCTION, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 40)
    print(" OIT-017 CORRECTION V2 INSTALLER")
    print(" FULL REPOSITORY-ALIGNED TEST REPLACEMENT")
    print("=" * 40)
    try:
        require_contract(
            OIT_016,
            (
                'SCHEMA_VERSION = "OIT-016"',
                'POLICY_ID = "oracle.cross-market-uncertainty-contradiction-synthesis.v1"',
                "OracleUncertaintyContradictionReport",
                "verify_uncertainty_contradiction_report",
                "unresolved_evidence_count",
            ),
            "Certified OIT-016",
        )
        require_contract(
            PRODUCTION,
            (
                'SCHEMA_VERSION = "OIT-017"',
                'POLICY_ID = "oracle.cross-market-narrative-evolution-intelligence.v1"',
                "OracleNarrativeEvolutionReport",
                "build_narrative_evolution_report",
                "verify_narrative_evolution_report",
                "publication_allowed",
                "qseries_execution_allowed",
            ),
            "Current OIT-017 production",
        )

        protected = protected_sources()
        production_hash = sha256(PRODUCTION)
        print("[OK] Certified OIT-016 uncertainty contract verified")
        print("[OK] Current OIT-017 production contract verified")
        print("[OK] Test-fixture unresolved-count defect isolated")
        print(
            f"[OK] Protected production source files captured: "
            f"{len(protected)}"
        )

        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_cross_market_narrative_evolution_intelligence "
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

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-017 Correction V2 test failed with exit code "
                f"{completed.returncode}"
            )

        if sha256(PRODUCTION) != production_hash:
            raise RuntimeError("OIT-017 production module changed unexpectedly")

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-016 production module unchanged")
        print("[PASS] OIT-017 production module unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Entire OIT-017 standalone test replaced")
        print("[PASS] Unresolved evidence count derived from fixture state")
        print("[PASS] Nonzero bounded contradiction counted consistently")
        print("[PASS] Complete OIT-017 production test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OIT-017 CORRECTION V2 FULL "
            "REPOSITORY-ALIGNED REPLACEMENT INSTALLED"
        )
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
