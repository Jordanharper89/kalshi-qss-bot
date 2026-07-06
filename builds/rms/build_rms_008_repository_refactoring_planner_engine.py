from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_refactoring_planner_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_008_repository_refactoring_planner_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-008"
ENGINE_NAME = "Repository Refactoring Planner Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryRefactoringStep:
    step_id: str
    phase: str
    title: str
    action: str
    target: str
    risk_level: str
    requires_manual_review: bool
    reason: str


@dataclass(frozen=True)
class RepositoryRefactoringPlanResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_count: int
    step_count: int
    manual_review_count: int
    approved_move_count: int
    blocked_move_count: int
    steps: List[RepositoryRefactoringStep]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_count": self.input_count,
            "step_count": self.step_count,
            "manual_review_count": self.manual_review_count,
            "approved_move_count": self.approved_move_count,
            "blocked_move_count": self.blocked_move_count,
            "steps": [asdict(step) for step in self.steps],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryRefactoringPlannerEngine:
    def plan(self, safe_move_validation: Any) -> RepositoryRefactoringPlanResult:
        validations = self._extract_validations(safe_move_validation)
        steps: List[RepositoryRefactoringStep] = []

        steps.append(
            RepositoryRefactoringStep(
                step_id="RMS008_STEP_000_BASELINE",
                phase="phase_0_baseline",
                title="Create Git checkpoint before repository refactor.",
                action="git_checkpoint",
                target="repository",
                risk_level="low",
                requires_manual_review=False,
                reason="A clean checkpoint is required before any physical move or refactor.",
            )
        )

        idx = 1
        for raw in validations:
            item = self._to_mapping(raw)
            if not item:
                continue

            approved = bool(item.get("approved_for_move", False))
            blockers = list(item.get("blockers", []) or [])
            risk = str(item.get("risk_level", "medium"))
            path = str(item.get("path", ""))
            destination = str(item.get("destination", ""))
            phase = str(item.get("phase", "phase_unknown"))

            if approved:
                steps.append(
                    RepositoryRefactoringStep(
                        step_id=f"RMS008_STEP_{idx:03d}_APPROVED_MOVE",
                        phase="phase_1_approved_moves",
                        title=f"Move approved low-risk item: {path}",
                        action="move_after_checkpoint",
                        target=f"{path} -> {destination}",
                        risk_level=risk,
                        requires_manual_review=False,
                        reason="Safe move validator approved this item with no blockers.",
                    )
                )
            else:
                steps.append(
                    RepositoryRefactoringStep(
                        step_id=f"RMS008_STEP_{idx:03d}_MANUAL_REVIEW",
                        phase="phase_2_manual_review",
                        title=f"Manual review required: {path}",
                        action="manual_review_before_move",
                        target=path,
                        risk_level=risk,
                        requires_manual_review=True,
                        reason="Blocked by: " + ", ".join(blockers) if blockers else "Move was not approved by validator.",
                    )
                )
            idx += 1

        steps.append(
            RepositoryRefactoringStep(
                step_id=f"RMS008_STEP_{idx:03d}_VALIDATION_GATE",
                phase="phase_3_validation",
                title="Run repository validation gate after any approved refactor batch.",
                action="run_validation_gate",
                target="RMS-009",
                risk_level="low",
                requires_manual_review=False,
                reason="Every refactor batch must end with repository validation before continuing.",
            )
        )

        manual = sum(1 for step in steps if step.requires_manual_review)
        approved = sum(1 for step in steps if step.action == "move_after_checkpoint")
        blocked = manual

        return RepositoryRefactoringPlanResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_count=len(validations),
            step_count=len(steps),
            manual_review_count=manual,
            approved_move_count=approved,
            blocked_move_count=blocked,
            steps=steps,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "planner_is_advisory": True,
                "input_contract": "RepositorySafeMoveValidationResult compatible",
                "output_contract": "RepositoryRefactoringPlanResult",
            },
            explanation=(
                f"Generated {len(steps)} advisory refactoring step(s): "
                f"{approved} approved move step(s), {manual} manual review step(s). "
                "No files were moved, deleted, or modified."
            ),
        )

    def _extract_validations(self, result: Any) -> List[Any]:
        if result is None:
            return []
        if isinstance(result, Mapping):
            raw = result.get("validations", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, "validations"):
            raw = getattr(result, "validations")
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        return []

    def _to_mapping(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            mapped = item.to_dict()
            return dict(mapped) if isinstance(mapped, Mapping) else {}
        if hasattr(item, "__dict__"):
            return dict(vars(item))
        return {}


def plan_repository_refactor(safe_move_validation: Any) -> RepositoryRefactoringPlanResult:
    return RepositoryRefactoringPlannerEngine().plan(safe_move_validation)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryRefactoringStep",
    "RepositoryRefactoringPlanResult",
    "RepositoryRefactoringPlannerEngine",
    "plan_repository_refactor",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph
from qseries_v2.repository_management.repository_dependency_analysis_engine import analyze_repository_dependencies
from qseries_v2.repository_management.repository_migration_planner_engine import plan_repository_migration
from qseries_v2.repository_management.repository_safe_move_validator_engine import validate_repository_safe_moves
from qseries_v2.repository_management.repository_refactoring_planner_engine import plan_repository_refactor


def test_refactoring_planner_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    migration = plan_repository_migration(analysis)
    validation = validate_repository_safe_moves(migration)
    result = plan_repository_refactor(validation)

    assert result.engine_id == "RMS-008"
    assert result.input_count > 0
    assert result.step_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.steps[0].action == "git_checkpoint"


def test_approved_validation_creates_move_step():
    result = plan_repository_refactor(
        {
            "validations": [
                {
                    "path": "weather_engine.py",
                    "module_name": "weather_engine",
                    "phase": "phase_2_low_risk_leaf",
                    "action": "review_then_move",
                    "destination": "services/weather/",
                    "risk_level": "low",
                    "approved_for_move": True,
                    "blockers": [],
                }
            ]
        }
    )

    assert result.approved_move_count == 1
    assert any(step.action == "move_after_checkpoint" for step in result.steps)


def test_blocked_validation_creates_manual_review_step():
    result = plan_repository_refactor(
        {
            "validations": [
                {
                    "path": "oracle_alert_engine.py",
                    "module_name": "oracle_alert_engine",
                    "phase": "phase_4_legacy_oracle_review",
                    "action": "manual_review",
                    "destination": "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/",
                    "risk_level": "high",
                    "approved_for_move": False,
                    "blockers": ["high_risk_requires_manual_review"],
                }
            ]
        }
    )

    assert result.manual_review_count == 1
    assert any(step.requires_manual_review for step in result.steps)


if __name__ == "__main__":
    test_refactoring_planner_from_live_repo()
    test_approved_validation_creates_move_step()
    test_blocked_validation_creates_manual_review_step()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    migration = plan_repository_migration(analysis)
    validation = validate_repository_safe_moves(migration)
    result = plan_repository_refactor(validation)

    print("[PASS] RMS-008 Repository Refactoring Planner Engine")
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
    print(" RMS-008 INSTALLER")
    print(" Repository Refactoring Planner Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-008 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_008_repository_refactoring_planner_engine.py")


if __name__ == "__main__":
    main()