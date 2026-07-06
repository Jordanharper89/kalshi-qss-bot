from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_baseline_report_engine import generate_repository_baseline_report


def test_baseline_report_from_live_repo():
    result = generate_repository_baseline_report(ROOT)

    assert result.engine_id == "RMS-011"
    assert result.total_items > 0
    assert result.scanned_files > 0
    assert result.finding_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert "RMS-010" in result.telemetry["validated_chain"]


def test_baseline_report_is_serializable():
    result = generate_repository_baseline_report(ROOT)
    data = result.to_dict()

    assert data["engine_id"] == "RMS-011"
    assert "findings" in data
    assert "telemetry" in data


if __name__ == "__main__":
    test_baseline_report_from_live_repo()
    test_baseline_report_is_serializable()

    result = generate_repository_baseline_report(ROOT)
    print("[PASS] RMS-011 Repository Baseline Report Engine")
    print(result.to_dict())
