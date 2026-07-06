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
