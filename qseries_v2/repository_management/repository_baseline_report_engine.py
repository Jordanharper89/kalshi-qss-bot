from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-011"
ENGINE_NAME = "Repository Baseline Report Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryBaselineFinding:
    finding_id: str
    severity: str
    title: str
    detail: str
    recommendation: str


@dataclass(frozen=True)
class RepositoryBaselineReportResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    certified: bool
    total_items: int
    scanned_files: int
    high_risk_count: int
    approved_move_count: int
    blocked_move_count: int
    finding_count: int
    findings: List[RepositoryBaselineFinding]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "certified": self.certified,
            "total_items": self.total_items,
            "scanned_files": self.scanned_files,
            "high_risk_count": self.high_risk_count,
            "approved_move_count": self.approved_move_count,
            "blocked_move_count": self.blocked_move_count,
            "finding_count": self.finding_count,
            "findings": [asdict(f) for f in self.findings],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryBaselineReportEngine:
    def generate(self, root: str | Path = ".") -> RepositoryBaselineReportResult:
        from .repository_inventory_engine import scan_repository
        from .repository_classification_engine import classify_repository_inventory
        from .repository_cleanup_recommendation_engine import recommend_repository_cleanup
        from .repository_dependency_graph_engine import build_repository_dependency_graph
        from .repository_dependency_analysis_engine import analyze_repository_dependencies
        from .repository_migration_planner_engine import plan_repository_migration
        from .repository_safe_move_validator_engine import validate_repository_safe_moves
        from .repository_refactoring_planner_engine import plan_repository_refactor
        from .repository_integration_gate_engine import run_repository_integration_gate
        from .repository_certification_engine import certify_repository_management

        root_path = Path(root).resolve()

        inventory = scan_repository(root_path)
        classification = classify_repository_inventory(inventory)
        cleanup = recommend_repository_cleanup(classification)
        graph = build_repository_dependency_graph(root_path)
        analysis = analyze_repository_dependencies(graph)
        migration = plan_repository_migration(analysis)
        validation = validate_repository_safe_moves(migration)
        refactor = plan_repository_refactor(validation)
        gate = run_repository_integration_gate(root_path)
        certification = certify_repository_management(gate)

        findings: List[RepositoryBaselineFinding] = []

        if getattr(certification, "certified", False):
            findings.append(self._finding(
                "RMS011_CERTIFIED",
                "positive",
                "Repository Management subsystem certified.",
                "RMS-001 through RMS-010 are installed and integration-gated.",
                "Use RMS output as the source of truth before any repository migration.",
            ))
        else:
            findings.append(self._finding(
                "RMS011_NOT_CERTIFIED",
                "critical",
                "Repository Management subsystem is not certified.",
                "The certification engine did not certify the repository management chain.",
                "Fix RMS integration failures before moving files.",
            ))

        high_risk = int(getattr(analysis, "high_risk_count", 0))
        approved = int(getattr(validation, "approved_count", 0))
        blocked = int(getattr(validation, "blocked_count", 0))

        if high_risk > 0:
            findings.append(self._finding(
                "RMS011_HIGH_RISK_PRESENT",
                "warning",
                "High-risk modules are present.",
                f"{high_risk} high-risk dependency item(s) were detected.",
                "Do not move high-risk modules until dependency review is complete.",
            ))

        if approved > 0:
            findings.append(self._finding(
                "RMS011_APPROVED_MOVES_PRESENT",
                "info",
                "Approved move candidates exist.",
                f"{approved} item(s) were approved by the safe move validator.",
                "Move only in small batches after a Git checkpoint.",
            ))

        if blocked > 0:
            findings.append(self._finding(
                "RMS011_BLOCKED_MOVES_PRESENT",
                "warning",
                "Blocked move candidates exist.",
                f"{blocked} item(s) were blocked by the safe move validator.",
                "Resolve blockers before physical migration.",
            ))

        status = "certified" if getattr(certification, "certified", False) else "blocked"

        return RepositoryBaselineReportResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            certified=bool(getattr(certification, "certified", False)),
            total_items=int(getattr(inventory, "total_items", 0)),
            scanned_files=int(getattr(graph, "scanned_files", 0)),
            high_risk_count=high_risk,
            approved_move_count=approved,
            blocked_move_count=blocked,
            finding_count=len(findings),
            findings=findings,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "baseline_report_is_advisory": True,
                "validated_chain": [
                    "RMS-001", "RMS-002", "RMS-003", "RMS-004", "RMS-005",
                    "RMS-006", "RMS-007", "RMS-008", "RMS-009", "RMS-010",
                ],
            },
            explanation=(
                f"Generated repository baseline report with status {status}. "
                f"Items={getattr(inventory, 'total_items', 0)}, "
                f"Python files scanned={getattr(graph, 'scanned_files', 0)}, "
                f"high-risk={high_risk}, approved moves={approved}, blocked moves={blocked}. "
                "No files were moved, deleted, or modified."
            ),
        )

    def _finding(self, finding_id: str, severity: str, title: str, detail: str, recommendation: str) -> RepositoryBaselineFinding:
        return RepositoryBaselineFinding(
            finding_id=finding_id,
            severity=severity,
            title=title,
            detail=detail,
            recommendation=recommendation,
        )


def generate_repository_baseline_report(root: str | Path = ".") -> RepositoryBaselineReportResult:
    return RepositoryBaselineReportEngine().generate(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryBaselineFinding",
    "RepositoryBaselineReportResult",
    "RepositoryBaselineReportEngine",
    "generate_repository_baseline_report",
]
