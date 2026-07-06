from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_dependency_graph_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_004_repository_dependency_graph_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Set


ENGINE_ID = "RMS-004"
ENGINE_NAME = "Repository Dependency Graph Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryDependencyNode:
    path: str
    module_name: str
    imports: List[str]
    internal_imports: List[str]
    external_imports: List[str]
    parse_error: str | None = None


@dataclass(frozen=True)
class RepositoryDependencyGraphResult:
    engine_id: str
    engine_name: str
    engine_version: str
    root: str
    scanned_files: int
    parsed_files: int
    parse_error_count: int
    internal_dependency_count: int
    external_dependency_count: int
    orphan_count: int
    circular_reference_count: int
    nodes: List[RepositoryDependencyNode]
    orphan_modules: List[str]
    circular_references: List[List[str]]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "root": self.root,
            "scanned_files": self.scanned_files,
            "parsed_files": self.parsed_files,
            "parse_error_count": self.parse_error_count,
            "internal_dependency_count": self.internal_dependency_count,
            "external_dependency_count": self.external_dependency_count,
            "orphan_count": self.orphan_count,
            "circular_reference_count": self.circular_reference_count,
            "nodes": [asdict(node) for node in self.nodes],
            "orphan_modules": list(self.orphan_modules),
            "circular_references": [list(item) for item in self.circular_references],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryDependencyGraphEngine:
    def build_graph(self, root: str | Path = ".") -> RepositoryDependencyGraphResult:
        root_path = Path(root).resolve()
        py_files = self._python_files(root_path)

        known_modules = {self._module_name(path, root_path) for path in py_files}
        nodes: List[RepositoryDependencyNode] = []

        for file_path in py_files:
            module_name = self._module_name(file_path, root_path)
            imports: List[str] = []
            parse_error = None

            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"))
                imports = self._extract_imports(tree)
            except Exception as exc:
                parse_error = f"{type(exc).__name__}: {exc}"

            internal, external = self._split_imports(imports, known_modules)

            nodes.append(
                RepositoryDependencyNode(
                    path=str(file_path.relative_to(root_path)),
                    module_name=module_name,
                    imports=sorted(imports),
                    internal_imports=sorted(internal),
                    external_imports=sorted(external),
                    parse_error=parse_error,
                )
            )

        depended_on = set()
        for node in nodes:
            depended_on.update(node.internal_imports)

        orphan_modules = sorted(
            node.module_name
            for node in nodes
            if node.module_name not in depended_on and not node.module_name.endswith("__init__")
        )

        graph = {node.module_name: set(node.internal_imports) for node in nodes}
        circular_references = self._find_cycles(graph)

        parsed_files = sum(1 for node in nodes if node.parse_error is None)
        parse_error_count = sum(1 for node in nodes if node.parse_error is not None)
        internal_count = sum(len(node.internal_imports) for node in nodes)
        external_count = sum(len(node.external_imports) for node in nodes)

        return RepositoryDependencyGraphResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            root=str(root_path),
            scanned_files=len(py_files),
            parsed_files=parsed_files,
            parse_error_count=parse_error_count,
            internal_dependency_count=internal_count,
            external_dependency_count=external_count,
            orphan_count=len(orphan_modules),
            circular_reference_count=len(circular_references),
            nodes=nodes,
            orphan_modules=orphan_modules,
            circular_references=circular_references,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "read_only_scan": True,
                "output_contract": "RepositoryDependencyGraphResult",
            },
            explanation=(
                f"Scanned {len(py_files)} Python file(s), parsed {parsed_files}, "
                f"found {internal_count} internal dependency reference(s), "
                f"{external_count} external import reference(s), "
                f"{len(orphan_modules)} orphan candidate(s), and "
                f"{len(circular_references)} circular reference candidate(s)."
            ),
        )

    def _python_files(self, root: Path) -> List[Path]:
        excluded_parts = {
            ".git",
            "venv",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "runtime",
        }
        files: List[Path] = []
        for path in root.rglob("*.py"):
            parts = set(path.relative_to(root).parts)
            if parts.intersection(excluded_parts):
                continue
            if ".bak" in path.name.lower() or "backup" in path.name.lower():
                continue
            files.append(path)
        return sorted(files, key=lambda p: str(p).lower())

    def _module_name(self, path: Path, root: Path) -> str:
        relative = path.relative_to(root).with_suffix("")
        return ".".join(relative.parts)

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        imports: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name:
                        imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.level and node.level > 0:
                        imports.add("." * node.level + node.module)
                    else:
                        imports.add(node.module)

        return sorted(imports)

    def _split_imports(self, imports: Iterable[str], known_modules: Set[str]) -> tuple[List[str], List[str]]:
        internal: Set[str] = set()
        external: Set[str] = set()

        for item in imports:
            normalized = item.lstrip(".")
            matched = None

            for known in known_modules:
                if known == normalized or known.startswith(normalized + ".") or normalized.startswith(known + "."):
                    matched = known
                    break

            if matched:
                internal.add(matched)
            else:
                external.add(normalized)

        return sorted(internal), sorted(external)

    def _find_cycles(self, graph: Mapping[str, Set[str]]) -> List[List[str]]:
        cycles: List[List[str]] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()
        stack: List[str] = []

        def visit(node: str) -> None:
            if node in visiting:
                try:
                    index = stack.index(node)
                    cycle = stack[index:] + [node]
                    if cycle not in cycles:
                        cycles.append(cycle)
                except ValueError:
                    pass
                return

            if node in visited:
                return

            visiting.add(node)
            stack.append(node)

            for dep in graph.get(node, set()):
                if dep in graph:
                    visit(dep)

            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in sorted(graph):
            visit(node)

        return cycles


def build_repository_dependency_graph(root: str | Path = ".") -> RepositoryDependencyGraphResult:
    return RepositoryDependencyGraphEngine().build_graph(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryDependencyNode",
    "RepositoryDependencyGraphResult",
    "RepositoryDependencyGraphEngine",
    "build_repository_dependency_graph",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_dependency_graph_engine import build_repository_dependency_graph


def test_dependency_graph_scans_live_repo():
    result = build_repository_dependency_graph(ROOT)

    assert result.engine_id == "RMS-004"
    assert result.scanned_files > 0
    assert result.parsed_files > 0
    assert result.telemetry["does_not_modify_files"] is True
    assert result.telemetry["read_only_scan"] is True
    assert isinstance(result.nodes, list)


def test_dependency_graph_detects_internal_imports():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("import b\n", encoding="utf-8")
        (root / "b.py").write_text("VALUE = 1\n", encoding="utf-8")

        result = build_repository_dependency_graph(root)

        node_a = [node for node in result.nodes if node.module_name == "a"][0]
        assert "b" in node_a.internal_imports


def test_dependency_graph_detects_parse_errors():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "bad.py").write_text("def broken(:\n", encoding="utf-8")

        result = build_repository_dependency_graph(root)

        assert result.parse_error_count == 1
        assert result.nodes[0].parse_error is not None


if __name__ == "__main__":
    test_dependency_graph_scans_live_repo()
    test_dependency_graph_detects_internal_imports()
    test_dependency_graph_detects_parse_errors()

    result = build_repository_dependency_graph(ROOT)
    print("[PASS] RMS-004 Repository Dependency Graph Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    lines = [
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        "from .repository_classification_engine import RepositoryClassificationEngine, classify_repository_inventory\n",
        "from .repository_cleanup_recommendation_engine import RepositoryCleanupRecommendationEngine, recommend_repository_cleanup\n",
        "from .repository_dependency_graph_engine import RepositoryDependencyGraphEngine, build_repository_dependency_graph\n",
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
    print(" RMS-004 INSTALLER")
    print(" Repository Dependency Graph Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-004 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_004_repository_dependency_graph_engine.py")


if __name__ == "__main__":
    main()