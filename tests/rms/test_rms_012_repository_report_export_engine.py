from pathlib import Path
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_baseline_report_engine import generate_repository_baseline_report
from qseries_v2.repository_management.repository_report_export_engine import export_repository_report


def test_report_export_from_live_baseline():
    with tempfile.TemporaryDirectory() as tmp:
        report = generate_repository_baseline_report(ROOT)
        output = Path(tmp) / "repository_baseline_report.json"
        result = export_repository_report(report, output)

        assert result.engine_id == "RMS-012"
        assert result.exported is True
        assert result.bytes_written > 0
        assert output.exists()
        assert result.telemetry["does_not_move_files"] is True


def test_exported_json_is_readable():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "report.json"
        result = export_repository_report({"status": "ok", "value": 1}, output)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["status"] == "ok"
        assert data["value"] == 1
        assert result.status == "exported"


if __name__ == "__main__":
    test_report_export_from_live_baseline()
    test_exported_json_is_readable()

    report = generate_repository_baseline_report(ROOT)
    output = ROOT / "architecture" / "RMS_BASELINE_REPORT.json"
    result = export_repository_report(report, output)

    print("[PASS] RMS-012 Repository Report Export Engine")
    print(result.to_dict())
