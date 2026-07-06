from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-007"
ENGINE_NAME = "Repository Safe Move Validator Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositorySafeMoveValidation:
    path: str
    module_name: str
    phase: str
    action: str
    destination: str
    risk_level: str
    approved_for_move: bool
    blocker_count: int
    blockers: List[str]


@dataclass(frozen=True)
class RepositorySafeMoveValidationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_count: int
    approved_count: int
    blocked_count: int
    validations: List[RepositorySafeMoveValidation]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_count": self.input_count,
            "approved_count": self.approved_count,
            "blocked_count": self.blocked_count,
            "validations": [asdict(item) for item in self.validations],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositorySafeMoveValidatorEngine:
    def validate(self, migration_plan: Any) -> RepositorySafeMoveValidationResult:
        items = self._extract_items(migration_plan)
        validations: List[RepositorySafeMoveValidation] = []

        for raw in items:
            item = self._to_mapping(raw)
            if not item:
                continue
            validations.append(self._validate_one(item))

        approved = sum(1 for item in validations if item.approved_for_move)
        blocked = len(validations) - approved

        return RepositorySafeMoveValidationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_count=len(items),
            approved_count=approved,
            blocked_count=blocked,
            validations=validations,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "validator_is_advisory": True,
                "input_contract": "RepositoryMigrationPlanResult compatible",
                "output_contract": "RepositorySafeMoveValidationResult",
            },
            explanation=(
                f"Validated {len(validations)} migration plan item(s). "
                f"Approved={approved}, blocked={blocked}. "
                "This validator is advisory only and performs no file operations."
            ),
        )

    def _validate_one(self, item: Mapping[str, Any]) -> RepositorySafeMoveValidation:
        path = str(item.get("path", ""))
        module_name = str(item.get("module_name", ""))
        phase = str(item.get("phase", ""))
        action = str(item.get("action", ""))
        destination = str(item.get("destination", ""))
        risk_level = str(item.get("risk_level", "medium"))

        blockers: List[str] = []

        if not path:
            blockers.append("missing_source_path")
        if not module_name:
            blockers.append("missing_module_name")
        if not destination or destination in {"review", "quarantine/review"}:
            blockers.append("destination_not_final")
        if risk_level == "high":
            blockers.append("high_risk_requires_manual_review")
        if phase in {"phase_4_legacy_oracle_review", "phase_5_dependency_hubs", "phase_6_fix_required"}:
            blockers.append("phase_requires_manual_review")
        if action in {"manual_review", "fix_before_move", "migrate_late", "hold_archive"}:
            blockers.append("action_blocks_automatic_move")
        if " or " in destination:
            blockers.append("ambiguous_destination")
        if path.lower().startswith("archive") or "backup" in path.lower() or ".bak" in path.lower():
            blockers.append("archive_or_backup_not_auto_migrated")

        approved = len(blockers) == 0 and action in {
            "keep",
            "review_then_move",
            "move_after_import_update",
            "move_with_group",
        }

        return RepositorySafeMoveValidation(
            path=path,
            module_name=module_name,
            phase=phase,
            action=action,
            destination=destination,
            risk_level=risk_level,
            approved_for_move=approved,
            blocker_count=len(blockers),
            blockers=blockers,
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


def validate_repository_safe_moves(migration_plan: Any) -> RepositorySafeMoveValidationResult:
    return RepositorySafeMoveValidatorEngine().validate(migration_plan)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositorySafeMoveValidation",
    "RepositorySafeMoveValidationResult",
    "RepositorySafeMoveValidatorEngine",
    "validate_repository_safe_moves",
]
