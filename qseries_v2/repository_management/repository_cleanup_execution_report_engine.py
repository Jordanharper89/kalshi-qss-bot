from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-020"
ENGINE_NAME = "Repository Cleanup Execution Report Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class CleanupExecutionReportStep:
    step_id: str
    phase: str
    title: str
    command: str
    risk_level: str
    manual_review_required: bool
    reason: str


@dataclass(frozen=True)
class CleanupExecutionReportResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    ready_for_cleanup: bool
    artifact_count: int
    safety_gate_passed: bool
    step_count: int
    steps: List[CleanupExecutionReportStep]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "ready_for_cleanup": self.ready_for_cleanup,
            "artifact_count": self.artifact_count,
            "safety_gate_passed": self.safety_gate_passed,
            "step_count": self.step_count,
            "steps": [asdict(step) for step in self.steps],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryCleanupExecutionReportEngine:
    def generate(self, root: str | Path = ".") -> CleanupExecutionReportResult:
        from .repository_tracked_artifact_audit_engine import audit_repository_tracked_artifacts
        from .repository_artifact_cleanup_planner_engine import plan_repository_artifact_cleanup
        from .repository_artifact_cleanup_safety_gate_engine import run_repository_artifact_cleanup_safety_gate

        root_path = Path(root).resolve()

        audit = audit_repository_tracked_artifacts(root_path)
        plan = plan_repository_artifact_cleanup(audit)
        gate = run_repository_artifact_cleanup_safety_gate(plan)

        artifact_count = int(getattr(audit, "artifact_count", 0))
        gate_passed = bool(getattr(gate, "passed", False))

        steps: List[CleanupExecutionReportStep] = []

        steps.append(
            CleanupExecutionReportStep(
                step_id="RMS020_STEP_001_STATUS",
                phase="phase_0_status",
                title="Verify clean Git status before cleanup.",
                command="git status",
                risk_level="low",
                manual_review_required=False,
                reason="Never begin cleanup without checking current repository state.",
            )
        )

        steps.append(
            CleanupExecutionReportStep(
                step_id="RMS020_STEP_002_CHECKPOINT",
                phase="phase_0_checkpoint",
                title="Create pre-cleanup checkpoint commit if needed.",
                command='git commit -m "Pre artifact cleanup checkpoint"',
                risk_level="low",
                manual_review_required=True,
                reason="Only run if there are staged/unstaged changes that need preserving.",
            )
        )

        if artifact_count > 0 and gate_passed:
            steps.extend(self._cleanup_steps_from_plan(plan))
        elif artifact_count > 0:
            steps.append(
                CleanupExecutionReportStep(
                    step_id="RMS020_STEP_BLOCKED",
                    phase="phase_blocked",
                    title="Artifact cleanup blocked by safety gate.",
                    command="py tests\\rms\\test_rms_019_repository_artifact_cleanup_safety_gate_engine.py",
                    risk_level="high",
                    manual_review_required=True,
                    reason="Safety gate failed. Do not perform physical cleanup until blockers are resolved.",
                )
            )
        else:
            steps.append(
                CleanupExecutionReportStep(
                    step_id="RMS020_STEP_NO_ARTIFACTS",
                    phase="phase_clean",
                    title="No tracked artifacts require cleanup.",
                    command="git status",
                    risk_level="low",
                    manual_review_required=False,
                    reason="Tracked artifact audit found no cleanup targets.",
                )
            )

        steps.append(
            CleanupExecutionReportStep(
                step_id="RMS020_STEP_FINAL_STATUS",
                phase="phase_final_validation",
                title="Verify Git status after cleanup.",
                command="git status",
                risk_level="low",
                manual_review_required=False,
                reason="Confirm only intended cleanup changes are staged or unstaged.",
            )
        )

        steps.append(
            CleanupExecutionReportStep(
                step_id="RMS020_STEP_FINAL_COMMIT",
                phase="phase_final_validation",
                title="Commit artifact cleanup after review.",
                command='git add . && git commit -m "Repository artifact cleanup"',
                risk_level="medium",
                manual_review_required=True,
                reason="Commit only after reviewing git status and confirming no source code was accidentally removed.",
            )
        )

        ready = artifact_count > 0 and gate_passed
        status = "ready" if ready else "blocked" if artifact_count > 0 else "clean"

        return CleanupExecutionReportResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            ready_for_cleanup=ready,
            artifact_count=artifact_count,
            safety_gate_passed=gate_passed,
            step_count=len(steps),
            steps=steps,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "report_only": True,
                "validated_chain": ["RMS-017", "RMS-018", "RMS-019"],
                "root": str(root_path),
            },
            explanation=(
                f"Generated cleanup execution report with status {status}. "
                f"Tracked artifacts={artifact_count}, safety gate passed={gate_passed}. "
                "This report does not move, delete, or modify files."
            ),
        )

    def _cleanup_steps_from_plan(self, plan: Any) -> List[CleanupExecutionReportStep]:
        raw_items = getattr(plan, "items", [])
        steps: List[CleanupExecutionReportStep] = []

        for index, item in enumerate(raw_items, start=3):
            path = str(getattr(item, "path", ""))
            action = str(getattr(item, "action", ""))
            command = str(getattr(item, "command_hint", ""))
            phase = str(getattr(item, "phase", "phase_cleanup"))
            risk = str(getattr(item, "risk_level", "medium"))

            if not command:
                command = "manual review required"

            steps.append(
                CleanupExecutionReportStep(
                    step_id=f"RMS020_STEP_{index:03d}",
                    phase=phase,
                    title=f"Cleanup tracked artifact: {path}",
                    command=command,
                    risk_level=risk,
                    manual_review_required=action in {"review_fixture_or_untrack", "manual_review"},
                    reason=f"Cleanup action from RMS-018 plan: {action}.",
                )
            )

        return steps


def generate_repository_cleanup_execution_report(root: str | Path = ".") -> CleanupExecutionReportResult:
    return RepositoryCleanupExecutionReportEngine().generate(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "CleanupExecutionReportStep",
    "CleanupExecutionReportResult",
    "RepositoryCleanupExecutionReportEngine",
    "generate_repository_cleanup_execution_report",
]
