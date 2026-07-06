from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "repository_management"
TEST_DIR = ROOT / "tests" / "rms"

MODULE = PKG / "repository_integration_gate_engine.py"
INIT = PKG / "__init__.py"
TEST = TEST_DIR / "test_rms_009_repository_integration_gate_engine.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-009"
ENGINE_NAME = "Repository Integration Gate Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RepositoryIntegrationGateCheck:
    check_id: str
    status: str
    detail: str


@dataclass(frozen=True)
class RepositoryIntegrationGateResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    passed: bool
    check_count: int
    pass_count: int
    fail_count: int
    checks: List[RepositoryIntegrationGateCheck]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "passed": self.passed,
            "check_count": self.check_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "checks": [asdict(check) for check in self.checks],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryIntegrationGateEngine:
    def run(self, root: str | Path = ".") -> RepositoryIntegrationGateResult:
        root_path = Path(root).resolve()
        checks: List[RepositoryIntegrationGateCheck] = []

        checks.append(self._check_exists(root_path / "qseries_v2", "RMS009_QSERIES_V2_EXISTS", "qseries_v2 source tree exists."))
        checks.append(self._check_exists(root_path / "qseries_v2" / "repository_management", "RMS009_RMS_PACKAGE_EXISTS", "Repository management package exists."))
        checks.append(self._check_exists(root_path / "builds" / "rms", "RMS009_RMS_BUILDS_EXISTS", "RMS build installer folder exists."))
        checks.append(self._check_exists(root_path / "tests" / "rms", "RMS009_RMS_TESTS_EXISTS", "RMS tests folder exists."))
        checks.append(self._check_exists(root_path / ".gitignore", "RMS009_GITIGNORE_EXISTS", ".gitignore exists."))

        checks.extend(self._check_required_modules(root_path))
        checks.extend(self._check_required_tests(root_path))
        checks.extend(self._check_gitignore_patterns(root_path))

        fail_count = sum(1 for c in checks if c.status == "fail")
        pass_count = sum(1 for c in checks if c.status == "pass")
        passed = fail_count == 0
        status = "passed" if passed else "failed"

        return RepositoryIntegrationGateResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            passed=passed,
            check_count=len(checks),
            pass_count=pass_count,
            fail_count=fail_count,
            checks=checks,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "gate_type": "repository_integration",
                "validated_engines": ["RMS-001", "RMS-002", "RMS-003", "RMS-004", "RMS-005", "RMS-006", "RMS-007", "RMS-008"],
            },
            explanation=(
                f"Repository integration gate {status}: "
                f"{pass_count} passed, {fail_count} failed."
            ),
        )

    def _check_exists(self, path: Path, check_id: str, success_detail: str) -> RepositoryIntegrationGateCheck:
        if path.exists():
            return RepositoryIntegrationGateCheck(check_id, "pass", success_detail)
        return RepositoryIntegrationGateCheck(check_id, "fail", f"Missing required path: {path}")

    def _check_required_modules(self, root: Path) -> List[RepositoryIntegrationGateCheck]:
        names = [
            "repository_inventory_engine.py",
            "repository_classification_engine.py",
            "repository_cleanup_recommendation_engine.py",
            "repository_dependency_graph_engine.py",
            "repository_dependency_analysis_engine.py",
            "repository_migration_planner_engine.py",
            "repository_safe_move_validator_engine.py",
            "repository_refactoring_planner_engine.py",
        ]
        checks: List[RepositoryIntegrationGateCheck] = []
        base = root / "qseries_v2" / "repository_management"

        for index, name in enumerate(names, start=1):
            path = base / name
            rms_id = f"RMS-{index:03d}"
            if path.exists():
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_MODULE_{index:03d}", "pass", f"{rms_id} module exists: {name}"))
            else:
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_MODULE_{index:03d}", "fail", f"Missing {rms_id} module: {name}"))

        return checks

    def _check_required_tests(self, root: Path) -> List[RepositoryIntegrationGateCheck]:
        checks: List[RepositoryIntegrationGateCheck] = []
        base = root / "tests" / "rms"

        for index in range(1, 9):
            pattern = f"test_rms_{index:03d}_*.py"
            matches = list(base.glob(pattern)) if base.exists() else []
            if matches:
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_TEST_{index:03d}", "pass", f"RMS-{index:03d} test exists."))
            else:
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_TEST_{index:03d}", "fail", f"Missing RMS-{index:03d} test file."))

        return checks

    def _check_gitignore_patterns(self, root: Path) -> List[RepositoryIntegrationGateCheck]:
        required = ["venv/", "__pycache__/", ".env", "*.bak*", "runtime/", "*.csv"]
        gitignore = root / ".gitignore"

        if not gitignore.exists():
            return [RepositoryIntegrationGateCheck("RMS009_GITIGNORE_PATTERNS", "fail", ".gitignore missing; cannot verify patterns.")]

        text = gitignore.read_text(encoding="utf-8", errors="replace")
        checks: List[RepositoryIntegrationGateCheck] = []

        for pattern in required:
            if pattern in text:
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_GITIGNORE_{pattern.replace('*', 'STAR').replace('/', '_').replace('.', 'DOT')}", "pass", f".gitignore contains {pattern}"))
            else:
                checks.append(RepositoryIntegrationGateCheck(f"RMS009_GITIGNORE_{pattern.replace('*', 'STAR').replace('/', '_').replace('.', 'DOT')}", "fail", f".gitignore missing {pattern}"))

        return checks


def run_repository_integration_gate(root: str | Path = ".") -> RepositoryIntegrationGateResult:
    return RepositoryIntegrationGateEngine().run(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RepositoryIntegrationGateCheck",
    "RepositoryIntegrationGateResult",
    "RepositoryIntegrationGateEngine",
    "run_repository_integration_gate",
]
'''

TEST_CODE = r'''
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_integration_gate_engine import run_repository_integration_gate


def test_repository_integration_gate_from_live_repo():
    result = run_repository_integration_gate(ROOT)

    assert result.engine_id == "RMS-009"
    assert result.check_count > 0
    assert result.telemetry["does_not_move_files"] is True
    assert result.pass_count >= 1


def test_repository_integration_gate_detects_missing_repo():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_repository_integration_gate(tmp)

        assert result.passed is False
        assert result.fail_count > 0
        assert result.status == "failed"


def test_repository_integration_gate_result_is_serializable():
    result = run_repository_integration_gate(ROOT)
    data = result.to_dict()

    assert data["engine_id"] == "RMS-009"
    assert "checks" in data
    assert "telemetry" in data


if __name__ == "__main__":
    test_repository_integration_gate_from_live_repo()
    test_repository_integration_gate_detects_missing_repo()
    test_repository_integration_gate_result_is_serializable()

    result = run_repository_integration_gate(ROOT)
    print("[PASS] RMS-009 Repository Integration Gate Engine")
    print(result.to_dict())
'''


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    lines = [
        "from .repository_inventory_engine import RepositoryInventoryEngine, scan_repository\n",
        "from .repository_classification_engine import RepositoryClassificationEngine, classify_repository_inventory\n",
        "from .repository_cleanup_recommendation_engine import RepositoryCleanupRecommendationEngine, recommend_repository_cleanup\n",
        "from .repository_dependency_graph_engine import RepositoryDependencyGraphEngine, build_repository_dependency_graph\n",
        "from .repository_dependency_analysis_engine import RepositoryDependencyAnalysisEngine, analyze_repository_dependencies\n",
        "from .repository_migration_planner_engine import RepositoryMigrationPlannerEngine, plan_repository_migration\n",
        "from .repository_safe_move_validator_engine import RepositorySafeMoveValidatorEngine, validate_repository_safe_moves\n",
        "from .repository_refactoring_planner_engine import RepositoryRefactoringPlannerEngine, plan_repository_refactor\n",
        "from .repository_integration_gate_engine import RepositoryIntegrationGateEngine, run_repository_integration_gate\n",
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
    print(" RMS-009 INSTALLER")
    print(" Repository Integration Gate Engine")
    print("========================================")
    print(f"[OK] Wrote {MODULE}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print()
    print("[DONE] RMS-009 installed")
    print()
    print("Run:")
    print("py tests\\rms\\test_rms_009_repository_integration_gate_engine.py")


if __name__ == "__main__":
    main()