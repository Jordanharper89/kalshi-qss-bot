from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_inventory_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_001_repository_inventory_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


ENGINE_ID = "RMS-001"
ENGINE_NAME = "Repository Inventory Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryInventoryItem:
    path: str
    name: str
    kind: str
    category: str
    size_bytes: int


@dataclass(frozen=True)
class RepositoryInventoryResult:
    engine_id: str
    engine_name: str
    engine_version: str
    root: str
    total_items: int
    files: int
    folders: int
    categories: Dict[str, int]
    items: List[RepositoryInventoryItem]

    def to_dict(self) -> Dict:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "root": self.root,
            "total_items": self.total_items,
            "files": self.files,
            "folders": self.folders,
            "categories": dict(self.categories),
            "items": [asdict(item) for item in self.items],
        }


class RepositoryInventoryEngine:
    def scan(self, root: str | Path = ".") -> RepositoryInventoryResult:
        root_path = Path(root).resolve()
        items: List[RepositoryInventoryItem] = []

        for item in sorted(root_path.iterdir(), key=lambda p: p.name.lower()):
            if item.name == ".git":
                continue

            kind = "folder" if item.is_dir() else "file"
            category = self._category(item)
            size = 0 if item.is_dir() else item.stat().st_size

            items.append(
                RepositoryInventoryItem(
                    path=item.name,
                    name=item.name,
                    kind=kind,
                    category=category,
                    size_bytes=size,
                )
            )

        categories: Dict[str, int] = {}
        for item in items:
            categories[item.category] = categories.get(item.category, 0) + 1

        return RepositoryInventoryResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            root=str(root_path),
            total_items=len(items),
            files=sum(1 for item in items if item.kind == "file"),
            folders=sum(1 for item in items if item.kind == "folder"),
            categories=dict(sorted(categories.items())),
            items=items,
        )

    def _category(self, path: Path) -> str:
        name = path.name

        if path.is_dir():
            if name in {"qseries_v2", "services", "plugins", "sports", "oracle_data_providers"}:
                return "ACTIVE_SOURCE"
            if name == "oracle":
                return "LEGACY_REVIEW"
            if name == "builds":
                return "BUILD"
            if name == "tests":
                return "TEST"
            if name == "scripts":
                return "SCRIPT"
            if name in {"architecture", "docs"}:
                return "DOCUMENTATION"
            if name in {"runtime", "__pycache__", "venv", ".venv"}:
                return "RUNTIME_IGNORE"
            if name.startswith("BACKUP_BEFORE") or name == "archive":
                return "ARCHIVE"
            return "UNKNOWN_FOLDER"

        lower = name.lower()

        if lower in {".env"} or lower.endswith(".env"):
            return "SECRET_IGNORE"
        if lower == ".gitignore":
            return "CONFIG"
        if lower == "readme.md":
            return "DOCUMENTATION"
        if lower.startswith("repository_") and lower.endswith(".txt"):
            return "DOCUMENTATION"
        if ".bak" in lower or "backup" in lower:
            return "ARCHIVE"
        if lower.endswith(".json") or lower.endswith(".csv") or lower.endswith(".log"):
            return "RUNTIME_IGNORE"
        if lower.startswith("oracle_") and lower.endswith(".py"):
            return "LEGACY_ORACLE_REVIEW"
        if lower.startswith("build_") and lower.endswith(".py"):
            return "BUILD"
        if lower.startswith("test_") and lower.endswith(".py"):
            return "TEST"
        if lower.startswith("patch_") and lower.endswith(".py"):
            return "SCRIPT"
        if lower.startswith("inspect_") and lower.endswith(".py"):
            return "SCRIPT"
        if lower.startswith("run_") and lower.endswith((".py", ".bat")):
            return "SCRIPT"
        if lower.endswith(".py"):
            return "ROOT_SOURCE_REVIEW"
        return "UNKNOWN_FILE"


def scan_repository(root: str | Path = ".") -> RepositoryInventoryResult:
    return RepositoryInventoryEngine().scan(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryInventoryItem",
    "RepositoryInventoryResult",
    "RepositoryInventoryEngine",
    "scan_repository",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_inventory_engine import scan_repository


def test_repository_inventory_scans_root():
    result = scan_repository(ROOT)

    assert result.engine_id == "RMS-001"
    assert result.total_items > 0
    assert result.files >= 1
    assert result.folders >= 1
    assert ".git" not in [item.name for item in result.items]
    assert "qseries_v2" in [item.name for item in result.items]
    assert result.categories


if __name__ == "__main__":
    test_repository_inventory_scans_root()
    print("[PASS] RMS-001 Repository Inventory Engine")
    print(scan_repository(ROOT).to_dict())
'''


def main():
    PKG.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    INIT.write_text(
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        encoding="utf-8",
    )
    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")

    print("========================================")
    print(" RMS-001 INSTALLER")
    print(" Repository Inventory Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {INIT}")
    print(f"[OK] Wrote {TEST}")
    print()
    print("[DONE] RMS-001 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_001_repository_inventory_engine.py")


if __name__ == "__main__":
    main()