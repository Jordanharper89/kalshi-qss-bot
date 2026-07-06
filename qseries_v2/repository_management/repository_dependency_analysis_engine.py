from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping


ENGINE_ID = "RMS-005"
ENGINE_NAME = "Repository Dependency Analysis Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryDependencyAnalysisRecord:
    module_name: str
    path: str
    inbound_count: int
    outbound_internal_count: int
    outbound_external_count: int
    risk_level: str
    role: str
    migration_guidance: str
    reason: str


@dataclass(frozen=True)
class RepositoryDependencyAnalysisResult:
    engine_id: str
    engine_name: str
    engine_version: str
    input_nodes: int
    analyzed_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    orphan_count: int
    circular_reference_count: int
    records: List[RepositoryDependencyAnalysisRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "input_nodes": self.input_nodes,
            "analyzed_count": self.analyzed_count,
            "high_risk_count": self.high_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "low_risk_count": self.low_risk_count,
            "orphan_count": self.orphan_count,
            "circular_reference_count": self.circular_reference_count,
            "records": [asdict(record) for record in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryDependencyAnalysisEngine:
    def analyze(self, graph_result: Any) -> RepositoryDependencyAnalysisResult:
        nodes = self._extract_nodes(graph_result)
        circular_count = self._extract_int(graph_result, "circular_reference_count", 0)
        orphan_modules = set(self._extract_list(graph_result, "orphan_modules"))

        inbound: Dict[str, int] = {}
        node_maps: List[Dict[str, Any]] = []

        for node in nodes:
            mapped = self._to_mapping(node)
            if not mapped:
                continue
            node_maps.append(mapped)
            for dep in mapped.get("internal_imports", []) or []:
                inbound[str(dep)] = inbound.get(str(dep), 0) + 1

        records: List[RepositoryDependencyAnalysisRecord] = []
        for node in node_maps:
            module_name = str(node.get("module_name", ""))
            path = str(node.get("path", ""))
            internal = list(node.get("internal_imports", []) or [])
            external = list(node.get("external_imports", []) or [])
            parse_error = node.get("parse_error")

            inbound_count = inbound.get(module_name, 0)
            outbound_internal_count = len(internal)
            outbound_external_count = len(external)

            role, risk, guidance, reason = self._assess(
                module_name=module_name,
                path=path,
                inbound_count=inbound_count,
                outbound_internal_count=outbound_internal_count,
                outbound_external_count=outbound_external_count,
                is_orphan=module_name in orphan_modules,
                parse_error=parse_error,
            )

            records.append(
                RepositoryDependencyAnalysisRecord(
                    module_name=module_name,
                    path=path,
                    inbound_count=inbound_count,
                    outbound_internal_count=outbound_internal_count,
                    outbound_external_count=outbound_external_count,
                    risk_level=risk,
                    role=role,
                    migration_guidance=guidance,
                    reason=reason,
                )
            )

        records.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}.get(r.risk_level, 9), -r.inbound_count, r.module_name))

        high = sum(1 for r in records if r.risk_level == "high")
        medium = sum(1 for r in records if r.risk_level == "medium")
        low = sum(1 for r in records if r.risk_level == "low")

        return RepositoryDependencyAnalysisResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            input_nodes=len(nodes),
            analyzed_count=len(records),
            high_risk_count=high,
            medium_risk_count=medium,
            low_risk_count=low,
            orphan_count=len(orphan_modules),
            circular_reference_count=circular_count,
            records=records,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "analysis_only": True,
                "input_contract": "RepositoryDependencyGraphResult compatible",
                "output_contract": "RepositoryDependencyAnalysisResult",
            },
            explanation=(
                f"Analyzed {len(records)} dependency node(s). "
                f"High risk={high}, medium risk={medium}, low risk={low}, "
                f"orphans={len(orphan_modules)}, circular references={circular_count}. "
                "This engine is advisory only."
            ),
        )

    def _assess(
        self,
        module_name: str,
        path: str,
        inbound_count: int,
        outbound_internal_count: int,
        outbound_external_count: int,
        is_orphan: bool,
        parse_error: Any,
    ) -> tuple[str, str, str, str]:
        lower_path = path.lower()
        lower_module = module_name.lower()

        if parse_error:
            return (
                "parse_error",
                "high",
                "fix_before_migration",
                "Module could not be parsed and must be fixed or quarantined before dependency-safe migration.",
            )

        if "backup" in lower_path or ".bak" in lower_path or lower_path.startswith("archive"):
            return (
                "archived_or_backup",
                "low",
                "keep_ignored_or_archive",
                "Archived or backup module should not block active migration.",
            )

        if lower_path.startswith("tests") or "\\tests\\" in lower_path:
            return (
                "test",
                "low",
                "move_with_test_suite",
                "Test module should move only with its corresponding subsystem tests.",
            )

        if lower_path.startswith("builds") or "\\builds\\" in lower_path:
            return (
                "build_installer",
                "low",
                "keep_in_builds",
                "Build installer belongs in the builds subsystem.",
            )

        if inbound_count >= 10 or outbound_internal_count >= 10:
            return (
                "dependency_hub",
                "high",
                "migrate_late_after_dependents_are_mapped",
                "Module has heavy dependency traffic and should not be moved until imports are planned.",
            )

        if lower_module.startswith("oracle_"):
            return (
                "legacy_oracle",
                "high" if inbound_count > 0 or outbound_internal_count > 0 else "medium",
                "review_legacy_oracle_before_move",
                "Legacy Oracle module requires import review before migration.",
            )

        if is_orphan and outbound_internal_count == 0:
            return (
                "orphan_leaf",
                "low",
                "safe_review_candidate",
                "Module appears isolated with no inbound or internal outbound dependencies.",
            )

        if is_orphan:
            return (
                "orphan_with_dependencies",
                "medium",
                "review_before_move",
                "Module has no inbound dependencies but still depends on internal modules.",
            )

        if outbound_internal_count == 0:
            return (
                "leaf_dependency",
                "low",
                "safe_to_move_after_import_path_update",
                "Module is depended on but does not depend on other internal modules.",
            )

        return (
            "standard_module",
            "medium",
            "move_with_dependency_group",
            "Module participates in the dependency graph and should move with its dependency group.",
        )

    def _extract_nodes(self, result: Any) -> List[Any]:
        if result is None:
            return []
        if isinstance(result, Mapping):
            raw = result.get("nodes", [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, "nodes"):
            raw = getattr(result, "nodes")
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        return []

    def _extract_list(self, result: Any, key: str) -> List[Any]:
        if isinstance(result, Mapping):
            raw = result.get(key, [])
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        if hasattr(result, key):
            raw = getattr(result, key)
            return list(raw) if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)) else []
        return []

    def _extract_int(self, result: Any, key: str, default: int) -> int:
        try:
            if isinstance(result, Mapping):
                return int(result.get(key, default))
            if hasattr(result, key):
                return int(getattr(result, key))
        except Exception:
            return default
        return default

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


def analyze_repository_dependencies(graph_result: Any) -> RepositoryDependencyAnalysisResult:
    return RepositoryDependencyAnalysisEngine().analyze(graph_result)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryDependencyAnalysisRecord",
    "RepositoryDependencyAnalysisResult",
    "RepositoryDependencyAnalysisEngine",
    "analyze_repository_dependencies",
]
