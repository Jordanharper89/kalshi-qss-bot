from pathlib import Path

ROOT = Path.cwd()
OPS_DIR = ROOT / "qseries_v2" / "ops"
TEST_PATH = ROOT / "test_ops_004_runtime_path_configuration_engine.py"

OPS_DIR.mkdir(parents=True, exist_ok=True)

runtime_paths_code = r'''
"""
OPS-004 Runtime Path Configuration Engine

Canonical runtime path contract for Q Series.

All runtime databases, logs, cache files, state files, raw inputs, and
test artifacts must resolve through this module instead of hard-coded paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RuntimePathValidationResult:
    status: str
    runtime_root: str
    directories: Dict[str, str]
    databases: Dict[str, str]
    missing_directories: List[str]
    created_directories: List[str]
    errors: List[str]

    @property
    def ok(self) -> bool:
        return self.status == "ok"


class RuntimePaths:
    """
    Single source of truth for Q Series runtime paths.

    Environment override:
        QSERIES_RUNTIME_ROOT=C:/path/to/runtime

    Default:
        <repo_root>/runtime
    """

    ENV_RUNTIME_ROOT = "QSERIES_RUNTIME_ROOT"

    @staticmethod
    def repo_root() -> Path:
        here = Path(__file__).resolve()
        for parent in [here, *here.parents]:
            if (parent / "qseries_v2").exists():
                return parent
        return Path.cwd().resolve()

    @classmethod
    def runtime_root(cls) -> Path:
        override = os.environ.get(cls.ENV_RUNTIME_ROOT)
        if override:
            return Path(override).expanduser().resolve()
        return cls.repo_root() / "runtime"

    @classmethod
    def data_dir(cls) -> Path:
        return cls.runtime_root() / "data"

    @classmethod
    def raw_dir(cls) -> Path:
        return cls.runtime_root() / "raw"

    @classmethod
    def logs_dir(cls) -> Path:
        return cls.runtime_root() / "logs"

    @classmethod
    def cache_dir(cls) -> Path:
        return cls.runtime_root() / "cache"

    @classmethod
    def state_dir(cls) -> Path:
        return cls.runtime_root() / "state"

    @classmethod
    def test_data_dir(cls) -> Path:
        return cls.runtime_root() / "test-data"

    @classmethod
    def oracle_data_db(cls) -> Path:
        return cls.data_dir() / "oracle_data.db"

    @classmethod
    def oracle_memory_db(cls) -> Path:
        return cls.data_dir() / "oracle_memory.sqlite3"

    @classmethod
    def oracle_runtime_state_db(cls) -> Path:
        return cls.data_dir() / "oracle_runtime_state.sqlite3"

    @classmethod
    def qseries_history_db(cls) -> Path:
        return cls.data_dir() / "qseries_history.sqlite3"

    @classmethod
    def required_directories(cls) -> Dict[str, Path]:
        return {
            "runtime": cls.runtime_root(),
            "data": cls.data_dir(),
            "raw": cls.raw_dir(),
            "logs": cls.logs_dir(),
            "cache": cls.cache_dir(),
            "state": cls.state_dir(),
            "test-data": cls.test_data_dir(),
        }

    @classmethod
    def database_paths(cls) -> Dict[str, Path]:
        return {
            "oracle_data_db": cls.oracle_data_db(),
            "oracle_memory_db": cls.oracle_memory_db(),
            "oracle_runtime_state_db": cls.oracle_runtime_state_db(),
            "qseries_history_db": cls.qseries_history_db(),
        }

    @classmethod
    def ensure_runtime_layout(cls) -> RuntimePathValidationResult:
        created: List[str] = []
        errors: List[str] = []

        for name, path in cls.required_directories().items():
            try:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    created.append(name)
            except Exception as exc:
                errors.append(f"{name}: {exc}")

        return cls.validate(created_directories=created, errors=errors)

    @classmethod
    def validate(
        cls,
        created_directories: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> RuntimePathValidationResult:
        created_directories = created_directories or []
        errors = errors or []

        missing = [
            name for name, path in cls.required_directories().items()
            if not path.exists() or not path.is_dir()
        ]

        status = "ok" if not missing and not errors else "error"

        return RuntimePathValidationResult(
            status=status,
            runtime_root=str(cls.runtime_root()),
            directories={k: str(v) for k, v in cls.required_directories().items()},
            databases={k: str(v) for k, v in cls.database_paths().items()},
            missing_directories=missing,
            created_directories=created_directories,
            errors=errors,
        )


runtime_paths = RuntimePaths


def ensure_runtime_layout() -> RuntimePathValidationResult:
    return RuntimePaths.ensure_runtime_layout()


def validate_runtime_paths() -> RuntimePathValidationResult:
    return RuntimePaths.validate()
'''

test_code = r'''
from pathlib import Path
import tempfile
import os

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout, validate_runtime_paths


def test_ops_004_runtime_path_configuration_engine():
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
        os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

        try:
            result = ensure_runtime_layout()

            assert result.ok
            assert result.status == "ok"
            assert Path(result.runtime_root).exists()

            expected_dirs = {
                "runtime",
                "data",
                "raw",
                "logs",
                "cache",
                "state",
                "test-data",
            }

            assert set(result.directories.keys()) == expected_dirs

            for path in result.directories.values():
                assert Path(path).exists()
                assert Path(path).is_dir()

            dbs = result.databases

            assert dbs["oracle_data_db"].endswith("runtime/data/oracle_data.db") or dbs["oracle_data_db"].endswith("runtime\\data\\oracle_data.db")
            assert dbs["oracle_memory_db"].endswith("runtime/data/oracle_memory.sqlite3") or dbs["oracle_memory_db"].endswith("runtime\\data\\oracle_memory.sqlite3")
            assert dbs["oracle_runtime_state_db"].endswith("runtime/data/oracle_runtime_state.sqlite3") or dbs["oracle_runtime_state_db"].endswith("runtime\\data\\oracle_runtime_state.sqlite3")
            assert dbs["qseries_history_db"].endswith("runtime/data/qseries_history.sqlite3") or dbs["qseries_history_db"].endswith("runtime\\data\\qseries_history.sqlite3")

            second = validate_runtime_paths()
            assert second.ok
            assert second.missing_directories == []

            print("[PASS] OPS-004 Runtime Path Configuration Engine")
            print({
                "status": second.status,
                "runtime_root": second.runtime_root,
                "directories": second.directories,
                "databases": second.databases,
            })

        finally:
            if old is None:
                os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
            else:
                os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old


if __name__ == "__main__":
    test_ops_004_runtime_path_configuration_engine()
'''

init_path = OPS_DIR / "__init__.py"
runtime_path = OPS_DIR / "runtime_paths.py"

runtime_path.write_text(runtime_paths_code, encoding="utf-8")
TEST_PATH.write_text(test_code, encoding="utf-8")

existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""
export_line = "from .runtime_paths import RuntimePaths, runtime_paths, ensure_runtime_layout, validate_runtime_paths\n"

if export_line not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export_line, encoding="utf-8")

print("========================================")
print(" OPS-004 INSTALLER")
print(" Runtime Path Configuration Engine")
print("========================================")
print(f"[OK] Wrote {runtime_path}")
print(f"[OK] Wrote {TEST_PATH}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-004 installed")
print("")
print("Run:")
print("py test_ops_004_runtime_path_configuration_engine.py")