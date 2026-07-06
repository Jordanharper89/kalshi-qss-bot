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
