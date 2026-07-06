from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-019"
ENGINE_NAME = "Repository Artifact Cleanup Safety Gate Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ArtifactCleanupSafetyCheck:
    check_id: str
    status: str
    path: str
    detail: str


@dataclass(frozen=True)
class ArtifactCleanupSafetyGateResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    passed: bool
    input_count: int
    check_count: int
    pass_count: int
    fail_count: int
    checks: List[ArtifactCleanupSafetyCheck]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "passed": self.passed,
            "input_count": self.input_count,
            "check_count": self.check_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "checks": [asdict(check) for check in self.checks],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryArtifactCleanupSafetyGateEngine:
    def run(self, cleanup_plan: Any) -> ArtifactCleanupSafetyGateResult:
        items = self._extract_items(cleanup_plan)
        checks: List[ArtifactCleanupSafetyCheck] = []

        for index, raw in enumerate(items, start=1):
            item = self._to_mapping(raw)
            if not item:
                checks.append(
                    ArtifactCleanupSafetyCheck(
                        check_id=f"RMS019_ITEM_{index:03d}_PARSE",
                        status="fail",
                        path="",
                        detail="Cleanup plan item could not be parsed.",
                    )
                )
                continue

            checks.extend(self._checks_for_item(index, item))

        fail_count = sum(1 for check in checks if check.status == "fail")
        pass_count = sum(1 for check in checks if check.status == "pass")
        passed = fail_count == 0
        status = "passed" if passed else "blocked"

        return ArtifactCleanupSafetyGateResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            passed=passed,
            input_count=len(items),
            check_count=len(checks),
            pass_count=pass_count,
            fail_count=fail_count,
            checks=checks,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "safety_gate_only": True,
                "input_contract": "ArtifactCleanupPlanResult compatible",
                "output_contract": "ArtifactCleanupSafetyGateResult",
            },
            explanation=(
                f"Artifact cleanup safety gate {status}: "
                f"{pass_count} passed, {fail_count} failed across {len(items)} plan item(s). "
                "No files were moved, deleted, or modified."
            ),
        )

    def _checks_for_item(self, index: int, item: Mapping[str, Any]) -> List[ArtifactCleanupSafetyCheck]:
        checks: List[ArtifactCleanupSafetyCheck] = []

        path = str(item.get("path", ""))
        action = str(item.get("action", ""))
        destination = str(item.get("destination", ""))
        phase = str(item.get("phase", ""))
        risk_level = str(item.get("risk_level", ""))
        command_hint = str(item.get("command_hint", ""))

        checks.append(self._check(
            f"RMS019_ITEM_{index:03d}_PATH",
            bool(path),
            path,
            "Source path is present.",
            "Source path is missing.",
        ))

        checks.append(self._check(
            f"RMS019_ITEM_{index:03d}_ACTION",
            action in {
                "move_to_runtime_then_untrack",
                "remove_from_git_tracking",
                "review_fixture_or_untrack",
                "manual_review",
            },
            path,
            f"Action is recognized: {action}.",
            f"Action is not recognized or unsafe: {action}.",
        ))

        checks.append(self._check(
            f"RMS019_ITEM_{index:03d}_PHASE",
            phase.startswith("phase_"),
            path,
            f"Cleanup phase is valid: {phase}.",
            f"Cleanup phase is missing or invalid: {phase}.",
        ))

        checks.append(self._check(
            f"RMS019_ITEM_{index:03d}_RISK",
            risk_level in {"low", "medium", "high"},
            path,
            f"Risk level is valid: {risk_level}.",
            f"Risk level is missing or invalid: {risk_level}.",
        ))

        if action == "move_to_runtime_then_untrack":
            checks.append(self._check(
                f"RMS019_ITEM_{index:03d}_DEST_RUNTIME",
                destination.startswith("runtime/") or destination.startswith("runtime\\"),
                path,
                f"Move destination is runtime-scoped: {destination}.",
                f"Move destination is not runtime-scoped: {destination}.",
            ))

        if action in {"remove_from_git_tracking", "move_to_runtime_then_untrack"}:
            checks.append(self._check(
                f"RMS019_ITEM_{index:03d}_COMMAND_GIT_RM_CACHED",
                "git rm --cached" in command_hint,
                path,
                "Command hint uses git rm --cached instead of deleting local file.",
                "Command hint does not include git rm --cached; cleanup may delete local data.",
            ))

        if action == "review_fixture_or_untrack":
            checks.append(self._check(
                f"RMS019_ITEM_{index:03d}_REVIEW_REQUIRED",
                True,
                path,
                "Raw sample cleanup requires manual fixture review.",
                "Raw sample cleanup review check failed.",
            ))

        checks.append(self._check(
            f"RMS019_ITEM_{index:03d}_NO_FORCE_DELETE",
            "del " not in command_hint.lower() and "rm -f" not in command_hint.lower(),
            path,
            "Command hint does not contain force-delete operation.",
            "Command hint contains a delete operation and is blocked.",
        ))

        return checks

    def _check(self, check_id: str, passed: bool, path: str, success: str, failure: str) -> ArtifactCleanupSafetyCheck:
        return ArtifactCleanupSafetyCheck(
            check_id=check_id,
            status="pass" if passed else "fail",
            path=path,
            detail=success if passed else failure,
        )

    def _extract_items(self, result: Any) -> List[Any]:
        if result is None:
            return []
        if isinstance(result, Mapping):
            raw = result.get("items", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, "items"):
            raw = getattr(result, "items")
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


def run_repository_artifact_cleanup_safety_gate(cleanup_plan: Any) -> ArtifactCleanupSafetyGateResult:
    return RepositoryArtifactCleanupSafetyGateEngine().run(cleanup_plan)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ArtifactCleanupSafetyCheck",
    "ArtifactCleanupSafetyGateResult",
    "RepositoryArtifactCleanupSafetyGateEngine",
    "run_repository_artifact_cleanup_safety_gate",
]
