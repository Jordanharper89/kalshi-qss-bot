from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_classification_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_002_repository_classification_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-002"
ENGINE_NAME = "Repository Classification Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryClassificationRecord:
    path: str
    name: str
    kind: str
    inventory_category: str
    classification: str
    owner: str
    recommended_home: str
    action: str
    reason: str


@dataclass(frozen=True)
class RepositoryClassificationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_count: int
    classified_count: int
    action_counts: Dict[str, int]
    classification_counts: Dict[str, int]
    records: List[RepositoryClassificationRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_count": self.input_count,
            "classified_count": self.classified_count,
            "action_counts": dict(self.action_counts),
            "classification_counts": dict(self.classification_counts),
            "records": [asdict(record) for record in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryClassificationEngine:
    def classify(self, inventory: Any) -> RepositoryClassificationResult:
        items = self._extract_items(inventory)
        records: List[RepositoryClassificationRecord] = []

        for item in items:
            item_map = self._to_mapping(item)
            if not item_map:
                continue
            records.append(self._classify_item(item_map))

        action_counts: Dict[str, int] = {}
        classification_counts: Dict[str, int] = {}

        for record in records:
            action_counts[record.action] = action_counts.get(record.action, 0) + 1
            classification_counts[record.classification] = classification_counts.get(record.classification, 0) + 1

        return RepositoryClassificationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_count=len(items),
            classified_count=len(records),
            action_counts=dict(sorted(action_counts.items())),
            classification_counts=dict(sorted(classification_counts.items())),
            records=records,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "classification_only": True,
                "input_contract": "RepositoryInventoryResult compatible",
                "output_contract": "RepositoryClassificationResult",
            },
            explanation=(
                f"Classified {len(records)} repository inventory item(s). "
                "This engine is advisory only and does not move, delete, or modify files."
            ),
        )

    def _classify_item(self, item: Mapping[str, Any]) -> RepositoryClassificationRecord:
        path = str(item.get("path", ""))
        name = str(item.get("name", path))
        kind = str(item.get("kind", "file"))
        inv = str(item.get("category", "UNKNOWN")).upper()
        lower = name.lower()

        if inv == "SECRET_IGNORE":
            return self._record(item, "SECRET", "Security", "ignored", "ignore", "Secret or environment file must never be committed.")

        if inv == "RUNTIME_IGNORE":
            return self._record(item, "RUNTIME", "Runtime", "runtime/", "ignore", "Runtime/generated file or folder should stay out of Git.")

        if inv == "ARCHIVE":
            return self._record(item, "ARCHIVE", "Archive", "archive/", "archive", "Backup or historical artifact.")

        if inv == "BUILD":
            return self._record(item, "BUILD_INSTALLER", "Build System", "builds/", "keep", "Installer/build artifact belongs under builds.")

        if inv == "TEST":
            return self._record(item, "TEST", "Test System", "tests/", "keep", "Test file or test folder belongs under tests.")

        if inv == "SCRIPT":
            return self._record(item, "SCRIPT", "Repository Tools", "scripts/", "keep", "Utility script belongs under scripts.")

        if inv in {"DOCUMENTATION", "CONFIG"}:
            return self._record(item, inv, "Repository", "architecture/ or root", "keep", "Documentation or repository config.")

        if name == "qseries_v2":
            return self._record(item, "ACTIVE_PLATFORM_SOURCE", "Q Series", "qseries_v2/", "keep", "Canonical active platform source tree.")

        if name == "oracle_data_providers":
            return self._record(item, "ACTIVE_PROVIDER_SOURCE", "Oracle Providers", "oracle_data_providers/", "keep", "Active provider support folder.")

        if name in {"services", "plugins", "sports"}:
            return self._record(item, "ACTIVE_SUPPORT_SOURCE", "Q Series Support", f"{name}/", "keep", "Active support source folder.")

        if name == "oracle" or inv == "LEGACY_REVIEW":
            return self._record(item, "LEGACY_ORACLE_FOLDER", "Legacy Oracle", "legacy/oracle/ or archive/", "review", "Legacy Oracle folder requires dependency review before migration.")

        if inv == "LEGACY_ORACLE_REVIEW":
            return self._record(item, "LEGACY_ORACLE_MODULE", "Legacy Oracle", "legacy/oracle/ or qseries_v2/oracle/", "review", "Root-level Oracle module may still support legacy workflows.")

        if inv == "ROOT_SOURCE_REVIEW":
            owner, home = self._root_source_owner(name)
            return self._record(item, "ROOT_SOURCE_MODULE", owner, home, "review", "Root-level source module requires classification before migration.")

        if name in {"10", "30", "45", "60", "70"}:
            return self._record(item, "ACCIDENTAL_JUNK", "Repository", "none", "delete_candidate", "Zero-byte numeric artifact appears accidental.")

        if lower.endswith(".py"):
            return self._record(item, "PYTHON_REVIEW", "Unknown", "review", "review", "Python file requires manual classification.")

        return self._record(item, "UNKNOWN", "Unknown", "review", "review", "Item requires manual review.")

    def _root_source_owner(self, name: str) -> tuple[str, str]:
        lower = name.lower()

        if "telegram" in lower:
            return "Telegram App", "apps/telegram/ or qseries_v2/"
        if "kalshi" in lower or "kalsi" in lower:
            return "Kalshi Integration", "integrations/kalshi/ or qseries_v2/adapters/"
        if "weather" in lower:
            return "Weather Provider", "services/weather/"
        if "sport" in lower or "mlb" in lower:
            return "Sports", "sports/"
        if "position" in lower or "order" in lower or "trade" in lower:
            return "Q Series Execution", "qseries_v2/execution/"
        if "strategy" in lower or "edge" in lower or "probability" in lower or "grading" in lower:
            return "Strategy Intelligence", "qseries_v2/strategy/"
        if "ai_" in lower or "research" in lower:
            return "AI Research", "services/ai/"
        return "Q Series Root Review", "qseries_v2/ or scripts/"

    def _record(
        self,
        item: Mapping[str, Any],
        classification: str,
        owner: str,
        home: str,
        action: str,
        reason: str,
    ) -> RepositoryClassificationRecord:
        return RepositoryClassificationRecord(
            path=str(item.get("path", "")),
            name=str(item.get("name", item.get("path", ""))),
            kind=str(item.get("kind", "file")),
            inventory_category=str(item.get("category", "UNKNOWN")),
            classification=classification,
            owner=owner,
            recommended_home=home,
            action=action,
            reason=reason,
        )

    def _extract_items(self, inventory: Any) -> List[Any]:
        if inventory is None:
            return []
        if isinstance(inventory, Mapping):
            raw = inventory.get("items", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(inventory, "items"):
            raw = getattr(inventory, "items")
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if isinstance(inventory, Iterable) and not isinstance(inventory, (str, bytes)):
            return list(inventory)
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


def classify_repository_inventory(inventory: Any) -> RepositoryClassificationResult:
    return RepositoryClassificationEngine().classify(inventory)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryClassificationRecord",
    "RepositoryClassificationResult",
    "RepositoryClassificationEngine",
    "classify_repository_inventory",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_inventory_engine import scan_repository
from qseries_v2.repository_management.repository_classification_engine import classify_repository_inventory


def test_classification_from_inventory():
    inventory = scan_repository(ROOT)
    result = classify_repository_inventory(inventory)

    assert result.engine_id == "RMS-002"
    assert result.input_count > 0
    assert result.classified_count > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True
    assert result.action_counts


def test_secret_and_runtime_are_ignored():
    result = classify_repository_inventory(
        {
            "items": [
                {"path": ".env", "name": ".env", "kind": "file", "category": "SECRET_IGNORE"},
                {"path": "positions.json", "name": "positions.json", "kind": "file", "category": "RUNTIME_IGNORE"},
            ]
        }
    )

    assert result.records[0].classification == "SECRET"
    assert result.records[0].action == "ignore"
    assert result.records[1].classification == "RUNTIME"
    assert result.records[1].action == "ignore"


def test_numeric_junk_is_delete_candidate():
    result = classify_repository_inventory(
        {"items": [{"path": "10", "name": "10", "kind": "file", "category": "UNKNOWN_FILE"}]}
    )

    assert result.records[0].classification == "ACCIDENTAL_JUNK"
    assert result.records[0].action == "delete_candidate"


if __name__ == "__main__":
    test_classification_from_inventory()
    test_secret_and_runtime_are_ignored()
    test_numeric_junk_is_delete_candidate()
    inventory = scan_repository(ROOT)
    result = classify_repository_inventory(inventory)
    print("[PASS] RMS-002 Repository Classification Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    lines = [
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        "from .repository_classification_engine import RepositoryClassificationEngine, classify_repository_inventory\n",
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
    print(" RMS-002 INSTALLER")
    print(" Repository Classification Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-002 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_002_repository_classification_engine.py")


if __name__ == "__main__":
    main()