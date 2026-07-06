from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_report_export_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_012_repository_report_export_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict


ENGINE_ID = "RMS-012"
ENGINE_NAME = "Repository Report Export Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryReportExportResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    exported: bool
    output_path: str
    bytes_written: int
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "exported": self.exported,
            "output_path": self.output_path,
            "bytes_written": self.bytes_written,
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryReportExportEngine:
    def export(self, report: Any, output_path: str | Path) -> RepositoryReportExportResult:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        data = self._to_dict(report)
        text = json.dumps(data, indent=2, sort_keys=True)
        target.write_text(text + "\n", encoding="utf-8")

        size = target.stat().st_size

        return RepositoryReportExportResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status="exported",
            exported=True,
            output_path=str(target),
            bytes_written=size,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "export_only": True,
                "canonical_input": "RepositoryBaselineReportResult compatible",
                "canonical_output": "RepositoryReportExportResult",
            },
            explanation=f"Exported repository report to {target} with {size} byte(s) written.",
        )

    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return dict(obj)
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            data = obj.to_dict()
            return dict(data) if isinstance(data, dict) else {}
        if hasattr(obj, "__dict__"):
            return dict(vars(obj))
        return {"value": str(obj)}


def export_repository_report(report: Any, output_path: str | Path) -> RepositoryReportExportResult:
    return RepositoryReportExportEngine().export(report, output_path)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryReportExportResult",
    "RepositoryReportExportEngine",
    "export_repository_report",
]
'''

TEST_CODE = r'''
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
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .repository_report_export_engine import RepositoryReportExportEngine, export_repository_report\n"
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
    print(" RMS-012 INSTALLER")
    print(" Repository Report Export Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-012 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_012_repository_report_export_engine.py")


if __name__ == "__main__":
    main()