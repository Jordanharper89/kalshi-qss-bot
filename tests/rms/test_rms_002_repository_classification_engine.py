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
