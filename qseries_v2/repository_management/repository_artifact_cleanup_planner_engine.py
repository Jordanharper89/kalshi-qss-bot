from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-018"
ENGINE_NAME = "Repository Artifact Cleanup Planner Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ArtifactCleanupPlanItem:
    path: str
    artifact_type: str
    phase: str
    action: str
    destination: str
    risk_level: str
    command_hint: str
    reason: str


@dataclass(frozen=True)
class ArtifactCleanupPlanResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    input_count: int
    plan_count: int
    phase_counts: Dict[str, int]
    items: List[ArtifactCleanupPlanItem]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "input_count": self.input_count,
            "plan_count": self.plan_count,
            "phase_counts": dict(self.phase_counts),
            "items": [asdict(item) for item in self.items],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryArtifactCleanupPlannerEngine:
    def plan(self, tracked_artifact_audit: Any) -> ArtifactCleanupPlanResult:
        records = self._extract_records(tracked_artifact_audit)
        items: List[ArtifactCleanupPlanItem] = []

        for raw in records:
            record = self._to_mapping(raw)
            if not record:
                continue
            items.append(self._plan_one(record))

        phase_order = {
            "phase_0_checkpoint": 0,
            "phase_1_runtime_databases": 1,
            "phase_2_test_databases": 2,
            "phase_3_raw_samples": 3,
            "phase_4_verify_gitignore": 4,
        }

        items.sort(key=lambda i: (phase_order.get(i.phase, 99), i.path))

        phase_counts: Dict[str, int] = {}
        for item in items:
            phase_counts[item.phase] = phase_counts.get(item.phase, 0) + 1

        status = "planned" if items else "clean"

        return ArtifactCleanupPlanResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            input_count=len(records),
            plan_count=len(items),
            phase_counts=dict(sorted(phase_counts.items())),
            items=items,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "planner_is_advisory": True,
                "input_contract": "TrackedArtifactAuditResult compatible",
                "output_contract": "ArtifactCleanupPlanResult",
            },
            explanation=(
                f"Generated {len(items)} advisory artifact cleanup plan item(s) "
                f"from {len(records)} tracked artifact record(s). No files were modified."
            ),
        )

    def _plan_one(self, record: Mapping[str, Any]) -> ArtifactCleanupPlanItem:
        path = str(record.get("path", ""))
        artifact_type = str(record.get("artifact_type", "unknown"))
        lower = path.lower().replace("\\", "/")

        if artifact_type == "tracked_database":
            if lower.startswith("qseries_v2/data/test_"):
                return self._item(
                    path,
                    artifact_type,
                    "phase_2_test_databases",
                    "remove_from_git_tracking",
                    "runtime/test-data/",
                    "medium",
                    f'git rm --cached "{path}"',
                    "Generated test database should not remain tracked; keep local copy ignored.",
                )

            return self._item(
                path,
                artifact_type,
                "phase_1_runtime_databases",
                "move_to_runtime_then_untrack",
                "runtime/data/",
                "medium",
                f'move "{path}" runtime\\data\\ && git rm --cached "{path}"',
                "Runtime database should live under runtime/data and be ignored.",
            )

        if artifact_type == "tracked_raw_sample":
            return self._item(
                path,
                artifact_type,
                "phase_3_raw_samples",
                "review_fixture_or_untrack",
                "architecture/fixtures/ or runtime/raw/",
                "medium",
                f'git rm --cached "{path}"',
                "Raw sample may be generated data; only keep if intentionally promoted to fixture.",
            )

        if artifact_type == "tracked_runtime_json":
            return self._item(
                path,
                artifact_type,
                "phase_3_raw_samples",
                "remove_from_git_tracking",
                "runtime/",
                "medium",
                f'git rm --cached "{path}"',
                "Runtime JSON state/sample should not remain tracked unless it is a fixture.",
            )

        return self._item(
            path,
            artifact_type,
            "phase_4_verify_gitignore",
            "manual_review",
            "review",
            "medium",
            "",
            "Artifact type requires manual review before cleanup.",
        )

    def _item(
        self,
        path: str,
        artifact_type: str,
        phase: str,
        action: str,
        destination: str,
        risk_level: str,
        command_hint: str,
        reason: str,
    ) -> ArtifactCleanupPlanItem:
        return ArtifactCleanupPlanItem(
            path=path,
            artifact_type=artifact_type,
            phase=phase,
            action=action,
            destination=destination,
            risk_level=risk_level,
            command_hint=command_hint,
            reason=reason,
        )

    def _extract_records(self, result: Any) -> List[Any]:
        if result is None:
            return []
        if isinstance(result, Mapping):
            raw = result.get("records", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, "records"):
            raw = getattr(result, "records")
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


def plan_repository_artifact_cleanup(tracked_artifact_audit: Any) -> ArtifactCleanupPlanResult:
    return RepositoryArtifactCleanupPlannerEngine().plan(tracked_artifact_audit)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ArtifactCleanupPlanItem",
    "ArtifactCleanupPlanResult",
    "RepositoryArtifactCleanupPlannerEngine",
    "plan_repository_artifact_cleanup",
]
