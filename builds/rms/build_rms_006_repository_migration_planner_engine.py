from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_migration_planner_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_006_repository_migration_planner_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-006"
ENGINE_NAME = "Repository Migration Planner Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryMigrationPlanItem:
    module_name: str
    path: str
    phase: str
    risk_level: str
    role: str
    action: str
    destination: str
    reason: str


@dataclass(frozen=True)
class RepositoryMigrationPlanResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_count: int
    plan_count: int
    phase_counts: Dict[str, int]
    risk_counts: Dict[str, int]
    items: List[RepositoryMigrationPlanItem]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_count": self.input_count,
            "plan_count": self.plan_count,
            "phase_counts": dict(self.phase_counts),
            "risk_counts": dict(self.risk_counts),
            "items": [asdict(item) for item in self.items],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryMigrationPlannerEngine:
    def plan(self, dependency_analysis: Any) -> RepositoryMigrationPlanResult:
        records = self._extract_records(dependency_analysis)
        items: List[RepositoryMigrationPlanItem] = []

        for raw in records:
            record = self._to_mapping(raw)
            if not record:
                continue
            items.append(self._plan_one(record))

        phase_order = {
            "phase_0_hold": 0,
            "phase_1_safe_support": 1,
            "phase_2_low_risk_leaf": 2,
            "phase_3_medium_grouped": 3,
            "phase_4_legacy_oracle_review": 4,
            "phase_5_dependency_hubs": 5,
            "phase_6_fix_required": 6,
        }
        risk_order = {"low": 0, "medium": 1, "high": 2}

        items.sort(
            key=lambda item: (
                phase_order.get(item.phase, 99),
                risk_order.get(item.risk_level, 99),
                item.path,
            )
        )

        phase_counts: Dict[str, int] = {}
        risk_counts: Dict[str, int] = {}

        for item in items:
            phase_counts[item.phase] = phase_counts.get(item.phase, 0) + 1
            risk_counts[item.risk_level] = risk_counts.get(item.risk_level, 0) + 1

        return RepositoryMigrationPlanResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_count=len(records),
            plan_count=len(items),
            phase_counts=dict(sorted(phase_counts.items())),
            risk_counts=dict(sorted(risk_counts.items())),
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
                "input_contract": "RepositoryDependencyAnalysisResult compatible",
                "output_contract": "RepositoryMigrationPlanResult",
            },
            explanation=(
                f"Generated {len(items)} advisory migration plan item(s). "
                "No files were moved, deleted, or modified."
            ),
        )

    def _plan_one(self, record: Mapping[str, Any]) -> RepositoryMigrationPlanItem:
        module_name = str(record.get("module_name", ""))
        path = str(record.get("path", ""))
        risk = str(record.get("risk_level", "medium"))
        role = str(record.get("role", "standard_module"))
        guidance = str(record.get("migration_guidance", "review_before_move"))
        lower = path.lower()

        if role == "parse_error":
            return self._item(record, "phase_6_fix_required", "fix_before_move", "quarantine/review", "Parse error must be fixed before migration.")

        if "backup" in lower or ".bak" in lower or lower.startswith("archive"):
            return self._item(record, "phase_0_hold", "hold_archive", "archive/", "Archive or backup artifact should not participate in active migration.")

        if lower.startswith("builds"):
            return self._item(record, "phase_1_safe_support", "keep", "builds/", "Build installer already belongs in builds.")

        if lower.startswith("tests"):
            return self._item(record, "phase_1_safe_support", "keep", "tests/", "Test file already belongs in tests.")

        if role == "orphan_leaf":
            return self._item(record, "phase_2_low_risk_leaf", "review_then_move", self._destination(path, module_name), "Low-risk orphan leaf can be moved after final review.")

        if role == "leaf_dependency":
            return self._item(record, "phase_2_low_risk_leaf", "move_after_import_update", self._destination(path, module_name), "Leaf dependency is low risk but inbound imports must be updated.")

        if role in {"standard_module", "orphan_with_dependencies"}:
            return self._item(record, "phase_3_medium_grouped", "move_with_group", self._destination(path, module_name), "Move with dependency group after import plan is generated.")

        if role == "legacy_oracle":
            return self._item(record, "phase_4_legacy_oracle_review", "manual_review", "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/", "Legacy Oracle requires manual review before migration.")

        if role == "dependency_hub":
            return self._item(record, "phase_5_dependency_hubs", "migrate_late", self._destination(path, module_name), "Dependency hub should be migrated late after dependent paths are stable.")

        return self._item(record, "phase_3_medium_grouped", guidance, self._destination(path, module_name), "Default advisory migration plan.")

    def _destination(self, path: str, module_name: str) -> str:
        lower = path.lower()
        name = lower.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]

        if lower.startswith("qseries_v2"):
            return "qseries_v2/"
        if "telegram" in name:
            return "qseries_v2/apps/telegram/"
        if "kalshi" in name or "kalsi" in name:
            return "qseries_v2/adapters/kalshi/"
        if "weather" in name:
            return "services/weather/"
        if "sport" in name or "mlb" in name:
            return "sports/"
        if "strategy" in name or "edge" in name or "probability" in name or "grading" in name:
            return "qseries_v2/strategy/"
        if "position" in name or "order" in name or "trade" in name:
            return "qseries_v2/execution/"
        if name.startswith("oracle_"):
            return "qseries_v2/oracle_intelligence/ or archive/legacy_oracle/"
        return "qseries_v2/review/"

    def _item(
        self,
        record: Mapping[str, Any],
        phase: str,
        action: str,
        destination: str,
        reason: str,
    ) -> RepositoryMigrationPlanItem:
        return RepositoryMigrationPlanItem(
            module_name=str(record.get("module_name", "")),
            path=str(record.get("path", "")),
            phase=phase,
            risk_level=str(record.get("risk_level", "medium")),
            role=str(record.get("role", "standard_module")),
            action=action,
            destination=destination,
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


def plan_repository_migration(dependency_analysis: Any) -> RepositoryMigrationPlanResult:
    return RepositoryMigrationPlannerEngine().plan(dependency_analysis)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryMigrationPlanItem",
    "RepositoryMigrationPlanResult",
    "RepositoryMigrationPlannerEngine",
    "plan_repository_migration",
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


def test_migration_planner_from_live_repo():
    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    result = plan_repository_migration(analysis)

    assert result.engine_id == "RMS-006"
    assert result.input_count > 0
    assert result.plan_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.phase_counts
    assert result.risk_counts


def test_parse_error_goes_to_fix_required():
    result = plan_repository_migration(
        {
            "records": [
                {
                    "module_name": "bad",
                    "path": "bad.py",
                    "risk_level": "high",
                    "role": "parse_error",
                    "migration_guidance": "fix_before_migration",
                }
            ]
        }
    )

    assert result.items[0].phase == "phase_6_fix_required"
    assert result.items[0].action == "fix_before_move"


def test_legacy_oracle_goes_to_legacy_review():
    result = plan_repository_migration(
        {
            "records": [
                {
                    "module_name": "oracle_alert_engine",
                    "path": "oracle_alert_engine.py",
                    "risk_level": "high",
                    "role": "legacy_oracle",
                    "migration_guidance": "review_legacy_oracle_before_move",
                }
            ]
        }
    )

    assert result.items[0].phase == "phase_4_legacy_oracle_review"
    assert result.items[0].action == "manual_review"


if __name__ == "__main__":
    test_migration_planner_from_live_repo()
    test_parse_error_goes_to_fix_required()
    test_legacy_oracle_goes_to_legacy_review()

    graph = build_repository_dependency_graph(ROOT)
    analysis = analyze_repository_dependencies(graph)
    result = plan_repository_migration(analysis)

    print("[PASS] RMS-006 Repository Migration Planner Engine")
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
    print(" RMS-006 INSTALLER")
    print(" Repository Migration Planner Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-006 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_006_repository_migration_planner_engine.py")


if __name__ == "__main__":
    main()