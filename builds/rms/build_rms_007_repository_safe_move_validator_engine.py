from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_safe_move_validator_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_007_repository_safe_move_validator_engine.py"

MODULE_CODE = r'''
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


def test_safe_move_validator_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    plan = plan_repository_migration(analysis)
    result = validate_repository_safe_moves(plan)

    assert result.engine_id == "RMS-007"
    assert result.input_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.validations


def test_high_risk_is_blocked():
    result = validate_repository_safe_moves(
        {
            "items": [
                {
                    "module_name": "oracle_alert_engine",
                    "path": "oracle_alert_engine.py",
                    "phase": "phase_4_legacy_oracle_review",
                    "risk_level": "high",
                    "action": "manual_review",
                    "destination": "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/",
                }
            ]
        }
    )

    assert result.validations[0].approved_for_move is False
    assert "high_risk_requires_manual_review" in result.validations[0].blockers
    assert "ambiguous_destination" in result.validations[0].blockers


def test_low_risk_final_destination_can_be_approved():
    result = validate_repository_safe_moves(
        {
            "items": [
                {
                    "module_name": "weather_engine",
                    "path": "weather_engine.py",
                    "phase": "phase_2_low_risk_leaf",
                    "risk_level": "low",
                    "action": "review_then_move",
                    "destination": "services/weather/",
                }
            ]
        }
    )

    assert result.validations[0].approved_for_move is True
    assert result.validations[0].blocker_count == 0


if __name__ == "__main__":
    test_safe_move_validator_from_live_repo()
    test_high_risk_is_blocked()
    test_low_risk_final_destination_can_be_approved()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    plan = plan_repository_migration(analysis)
    result = validate_repository_safe_moves(plan)

    print("[PASS] RMS-007 Repository Safe Move Validator Engine")
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
    print(" RMS-007 INSTALLER")
    print(" Repository Safe Move Validator Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-007 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_007_repository_safe_move_validator_engine.py")


if __name__ == "__main__":
    main()