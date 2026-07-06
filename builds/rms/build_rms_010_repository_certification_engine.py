from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_certification_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_010_repository_certification_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-010"
ENGINE_NAME = "Repository Certification Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryCertificationDecision:
    decision_id: str
    certified: bool
    certification_level: str
    confidence: float
    reason_codes: List[str]
    explanation: str


@dataclass(frozen=True)
class RepositoryCertificationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    certified: bool
    certification_level: str
    decision_count: int
    decisions: List[RepositoryCertificationDecision]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "certified": self.certified,
            "certification_level": self.certification_level,
            "decision_count": self.decision_count,
            "decisions": [asdict(d) for d in self.decisions],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryCertificationEngine:
    def certify(self, integration_gate_result: Any) -> RepositoryCertificationResult:
        gate = self._to_dict(integration_gate_result)
        passed = bool(gate.get("passed", False))
        pass_count = int(gate.get("pass_count", 0) or 0)
        fail_count = int(gate.get("fail_count", 0) or 0)
        check_count = int(gate.get("check_count", 0) or 0)

        reason_codes: List[str] = [
            "RMS_ADVISORY_ONLY",
            "NO_FILE_OPERATIONS",
            "REPOSITORY_ARCHITECTURE_SUPPORT",
        ]

        if passed:
            reason_codes.append("INTEGRATION_GATE_PASSED")
        else:
            reason_codes.append("INTEGRATION_GATE_FAILED")

        if fail_count == 0:
            reason_codes.append("ZERO_GATE_FAILURES")

        confidence = 0.0 if check_count <= 0 else round(pass_count / check_count, 4)

        certified = passed and fail_count == 0 and check_count >= 20
        if certified and confidence >= 1.0:
            level = "certified"
            status = "certified"
        elif passed:
            level = "provisional"
            status = "review"
        else:
            level = "not_certified"
            status = "blocked"

        decision = RepositoryCertificationDecision(
            decision_id="RMS010_REPOSITORY_MANAGEMENT_CERTIFICATION",
            certified=certified,
            certification_level=level,
            confidence=confidence,
            reason_codes=reason_codes,
            explanation=(
                f"Repository Management certification reviewed {check_count} gate check(s): "
                f"{pass_count} passed, {fail_count} failed. "
                f"Certification level={level}."
            ),
        )

        return RepositoryCertificationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            certified=certified,
            certification_level=level,
            decision_count=1,
            decisions=[decision],
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "certification_is_advisory": True,
                "input_engine_id": "RMS-009",
                "canonical_input": "RepositoryIntegrationGateResult compatible",
                "canonical_output": "RepositoryCertificationResult",
                "validated_engines": [
                    "RMS-001", "RMS-002", "RMS-003", "RMS-004", "RMS-005",
                    "RMS-006", "RMS-007", "RMS-008", "RMS-009"
                ],
            },
            explanation=(
                f"RMS-010 produced {level} certification with status {status}. "
                "Repository Management remains advisory and does not move, delete, or modify files."
            ),
        )

    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return dict(obj)
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            data = obj.to_dict()
            return dict(data) if isinstance(data, dict) else {}
        if hasattr(obj, "__dict__"):
            return dict(vars(obj))
        return {}


def certify_repository_management(integration_gate_result: Any) -> RepositoryCertificationResult:
    return RepositoryCertificationEngine().certify(integration_gate_result)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryCertificationDecision",
    "RepositoryCertificationResult",
    "RepositoryCertificationEngine",
    "certify_repository_management",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_integration_gate_engine import run_repository_integration_gate
from qseries_v2.repository_management.repository_certification_engine import certify_repository_management


def test_repository_certification_from_live_gate():
    gate = run_repository_integration_gate(ROOT)
    result = certify_repository_management(gate)

    assert result.engine_id == "RMS-010"
    assert result.decision_count == 1
    assert result.telemetry["does_not_move_files"] is True
    assert result.telemetry["certification_is_advisory"] is True


def test_passed_gate_certifies():
    result = certify_repository_management(
        {
            "passed": True,
            "check_count": 27,
            "pass_count": 27,
            "fail_count": 0,
        }
    )

    assert result.certified is True
    assert result.status == "certified"
    assert result.certification_level == "certified"


def test_failed_gate_blocks_certification():
    result = certify_repository_management(
        {
            "passed": False,
            "check_count": 27,
            "pass_count": 26,
            "fail_count": 1,
        }
    )

    assert result.certified is False
    assert result.status == "blocked"
    assert result.certification_level == "not_certified"


if __name__ == "__main__":
    test_repository_certification_from_live_gate()
    test_passed_gate_certifies()
    test_failed_gate_blocks_certification()

    gate = run_repository_integration_gate(ROOT)
    result = certify_repository_management(gate)

    print("[PASS] RMS-010 Repository Certification Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    lines = [
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        "from .repository_classification_engine import RepositoryClassificationEngine, classify_repository_inventory\n",
        "from .repository_cleanup_recommendation_engine import RepositoryCleanupRecommendationEngine, recommend_repository_cleanup\n",
        "from .repository_dependency_graph_engine import RepositoryDependencyGraphEngine, build_repository_dependency_graph\n",
        "from .repository_dependency_analysis_engine import RepositoryDependencyAnalysisEngine, analyze_repository_dependencies\n",
        "from .repository_migration_planner_engine import RepositoryMigrationPlannerEngine, plan_repository_migration\n",
        "from .repository_safe_move_validator_engine import RepositorySafeMoveValidatorEngine, validate_repository_safe_moves\n",
        "from .repository_refactoring_planner_engine import RepositoryRefactoringPlannerEngine, plan_repository_refactor\n",
        "from .repository_integration_gate_engine import RepositoryIntegrationGateEngine, run_repository_integration_gate\n",
        "from .repository_certification_engine import RepositoryCertificationEngine, certify_repository_management\n",
    ]
    for line in lines:
        if line not in existing:
            existing += line
    INIT.write_text(existing, encoding="utf-8")


def main():
    PKG.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    update_init()

    print("========================================")
    print(" RMS-010 INSTALLER")
    print(" Repository Certification Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-010 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_010_repository_certification_engine.py")


if __name__ == "__main__":
    main()