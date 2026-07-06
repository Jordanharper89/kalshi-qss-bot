from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
TEST = ROOT / "test_oi_202_replay_framework_smoke_integration_gate_v2.py"
MODULE = PKG / "replay_framework_smoke_integration_gate_v2.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-202 — Replay Framework Smoke Integration Gate V2

Validates the replay recommendation chain through OI-201.

This is a smoke integration gate, not an execution engine.
Oracle remains read-only. Q Series remains the only execution owner.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Tuple


ENGINE_ID = "OI-202"
ENGINE_NAME = "Replay Framework Smoke Integration Gate V2"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplaySmokeGateCheck:
    check_id: str
    status: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplaySmokeGateResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    passed: bool
    checks: Tuple[ReplaySmokeGateCheck, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class ReplayFrameworkSmokeIntegrationGateV2:
    def run(self) -> ReplaySmokeGateResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        checks: List[ReplaySmokeGateCheck] = []

        try:
            from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_engine import (
                rank_replay_recommendations,
            )
            checks.append(self._pass("OI202_IMPORT_OI198", "Imported OI-198 ranking engine."))
        except Exception as exc:
            checks.append(self._fail("OI202_IMPORT_OI198", f"Failed importing OI-198: {exc}"))
            return self._result(generated_at, checks)

        try:
            from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_analytics_engine import (
                analyze_replay_recommendation_rankings,
            )
            checks.append(self._pass("OI202_IMPORT_OI199", "Imported OI-199 ranking analytics engine."))
        except Exception as exc:
            checks.append(self._fail("OI202_IMPORT_OI199", f"Failed importing OI-199: {exc}"))
            return self._result(generated_at, checks)

        try:
            from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_intelligence_engine import (
                evaluate_replay_recommendation_ranking_intelligence,
            )
            checks.append(self._pass("OI202_IMPORT_OI200", "Imported OI-200 ranking intelligence engine."))
        except Exception as exc:
            checks.append(self._fail("OI202_IMPORT_OI200", f"Failed importing OI-200: {exc}"))
            return self._result(generated_at, checks)

        try:
            from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_certification_engine import (
                certify_replay_recommendation_ranking_intelligence,
            )
            checks.append(self._pass("OI202_IMPORT_OI201", "Imported OI-201 certification engine."))
        except Exception as exc:
            checks.append(self._fail("OI202_IMPORT_OI201", f"Failed importing OI-201: {exc}"))
            return self._result(generated_at, checks)

        recommendations = [
            {
                "recommendation_id": "gate_demo_strong",
                "market_id": "GATE-MARKET-1",
                "adapter_id": "adp.gate",
                "confidence": 0.95,
                "edge_pct": 25,
                "replay_quality": 0.92,
                "stability": 0.88,
                "explainability": 0.84,
            },
            {
                "recommendation_id": "gate_demo_watch",
                "market_id": "GATE-MARKET-2",
                "adapter_id": "adp.gate",
                "confidence": 0.66,
                "edge_pct": 8,
                "replay_quality": 0.61,
                "stability": 0.58,
                "explainability": 0.62,
            },
        ]

        ranking = rank_replay_recommendations(recommendations)
        ranking_map = ranking.to_dict()
        self._check_read_only(checks, ranking_map, "OI202_RANKING_READ_ONLY", "OI-198")
        self._check_execution_owner(checks, ranking_map, "OI202_RANKING_EXECUTION_OWNER", "OI-198")
        self._check_non_empty(checks, ranking_map.get("rankings"), "OI202_RANKING_OUTPUT", "OI-198 produced rankings.")

        analytics = analyze_replay_recommendation_rankings(ranking)
        analytics_map = analytics.to_dict()
        self._check_read_only(checks, analytics_map, "OI202_ANALYTICS_READ_ONLY", "OI-199")
        self._check_execution_owner(checks, analytics_map, "OI202_ANALYTICS_EXECUTION_OWNER", "OI-199")
        self._check_non_empty(checks, analytics_map.get("findings"), "OI202_ANALYTICS_FINDINGS", "OI-199 produced analytics findings.")

        intelligence = evaluate_replay_recommendation_ranking_intelligence(analytics)
        intelligence_map = intelligence.to_dict()
        self._check_read_only(checks, intelligence_map, "OI202_INTELLIGENCE_READ_ONLY", "OI-200")
        self._check_execution_owner(checks, intelligence_map, "OI202_INTELLIGENCE_EXECUTION_OWNER", "OI-200")
        self._check_non_empty(checks, intelligence_map.get("signals"), "OI202_INTELLIGENCE_SIGNALS", "OI-200 produced intelligence signals.")

        certification = certify_replay_recommendation_ranking_intelligence(intelligence)
        certification_map = certification.to_dict()
        self._check_read_only(checks, certification_map, "OI202_CERTIFICATION_READ_ONLY", "OI-201")
        self._check_execution_owner(checks, certification_map, "OI202_CERTIFICATION_EXECUTION_OWNER", "OI-201")
        self._check_non_empty(checks, certification_map.get("decisions"), "OI202_CERTIFICATION_DECISIONS", "OI-201 produced certification decisions.")

        if certification_map.get("certified") is True:
            checks.append(self._pass("OI202_END_TO_END_CERTIFIED", "End-to-end replay ranking certification completed."))
        else:
            checks.append(self._fail("OI202_END_TO_END_CERTIFIED", "Certification did not pass for smoke-gate strong replay sample."))

        return self._result(generated_at, checks)

    def _check_read_only(self, checks: List[ReplaySmokeGateCheck], payload: Mapping[str, Any], check_id: str, label: str) -> None:
        telemetry = payload.get("telemetry", {})
        if isinstance(telemetry, Mapping) and telemetry.get("read_only") is True:
            checks.append(self._pass(check_id, f"{label} preserved read-only telemetry."))
        else:
            checks.append(self._fail(check_id, f"{label} failed read-only telemetry validation."))

    def _check_execution_owner(self, checks: List[ReplaySmokeGateCheck], payload: Mapping[str, Any], check_id: str, label: str) -> None:
        telemetry = payload.get("telemetry", {})
        if isinstance(telemetry, Mapping) and telemetry.get("execution_owner") == "Q Series":
            checks.append(self._pass(check_id, f"{label} preserved Q Series execution ownership."))
        else:
            checks.append(self._fail(check_id, f"{label} failed Q Series execution ownership validation."))

    def _check_non_empty(self, checks: List[ReplaySmokeGateCheck], value: Any, check_id: str, detail: str) -> None:
        if value:
            checks.append(self._pass(check_id, detail))
        else:
            checks.append(self._fail(check_id, f"Expected non-empty value for {check_id}."))

    def _pass(self, check_id: str, detail: str) -> ReplaySmokeGateCheck:
        return ReplaySmokeGateCheck(check_id=check_id, status="pass", detail=detail)

    def _fail(self, check_id: str, detail: str) -> ReplaySmokeGateCheck:
        return ReplaySmokeGateCheck(check_id=check_id, status="fail", detail=detail)

    def _result(self, generated_at: str, checks: List[ReplaySmokeGateCheck]) -> ReplaySmokeGateResult:
        passed = all(check.status == "pass" for check in checks)
        status = "passed" if passed else "failed"
        return ReplaySmokeGateResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            passed=passed,
            checks=tuple(checks),
            telemetry={
                "engine_id": ENGINE_ID,
                "read_only": True,
                "oracle_role": "brain",
                "execution_owner": "Q Series",
                "does_not_execute": True,
                "does_not_route_orders": True,
                "does_not_manage_positions": True,
                "gate_type": "smoke_integration",
                "validated_modules": ["OI-198", "OI-199", "OI-200", "OI-201"],
                "canonical_flow": "ranking -> analytics -> intelligence -> certification",
            },
            explanation=(
                "Replay smoke integration gate validated the ranking recommendation chain. "
                "Oracle remained read-only and Q Series retained execution ownership."
                if passed else
                "Replay smoke integration gate failed. Stop building and repair contract drift before continuing."
            ),
        )


def run_replay_framework_smoke_integration_gate_v2() -> ReplaySmokeGateResult:
    return ReplayFrameworkSmokeIntegrationGateV2().run()


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplaySmokeGateCheck",
    "ReplaySmokeGateResult",
    "ReplayFrameworkSmokeIntegrationGateV2",
    "run_replay_framework_smoke_integration_gate_v2",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.replay_framework_smoke_integration_gate_v2 import (
    ENGINE_ID,
    ReplayFrameworkSmokeIntegrationGateV2,
    run_replay_framework_smoke_integration_gate_v2,
)


def test_replay_framework_smoke_gate_v2_passes():
    result = ReplayFrameworkSmokeIntegrationGateV2().run()

    assert result.engine_id == ENGINE_ID
    assert result.passed is True
    assert result.status == "passed"
    assert len(result.checks) >= 10
    assert all(check.status == "pass" for check in result.checks)
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert "OI-201" in result.telemetry["validated_modules"]


def test_wrapper_returns_gate_result():
    result = run_replay_framework_smoke_integration_gate_v2()

    assert result.passed is True
    assert result.telemetry["gate_type"] == "smoke_integration"
    assert result.telemetry["canonical_flow"] == "ranking -> analytics -> intelligence -> certification"


if __name__ == "__main__":
    test_replay_framework_smoke_gate_v2_passes()
    test_wrapper_returns_gate_result()
    print("[PASS] OI-202 Replay Framework Smoke Integration Gate V2")
    print(run_replay_framework_smoke_integration_gate_v2().to_dict())
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .replay_framework_smoke_integration_gate_v2 import "
        "ReplayFrameworkSmokeIntegrationGateV2, "
        "run_replay_framework_smoke_integration_gate_v2\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-202 INSTALLER")
    print(" Replay Framework Smoke Integration Gate V2")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-202 installed")
    print()
    print("Run:")
    print("py test_oi_202_replay_framework_smoke_integration_gate_v2.py")


if __name__ == "__main__":
    main()