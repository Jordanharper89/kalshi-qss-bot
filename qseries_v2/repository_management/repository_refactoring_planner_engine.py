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
