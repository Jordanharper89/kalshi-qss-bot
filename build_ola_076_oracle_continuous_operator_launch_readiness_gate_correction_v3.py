from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_continuous_operator_launch_readiness_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_076_oracle_continuous_operator_launch_readiness_gate.py"
)


PRODUCTION_SOURCE = r'''"""
OLA-076
Oracle Continuous Operator Launch Readiness Gate
Production Correction V3

This module validates the exact on-disk OLA-075 and OLA-074 dependency
sources before granting a read-only Oracle continuous-operator readiness
attestation.

Correction V3 permanently prevents stale dynamic dependency reuse.

Every dependency load:

1. invalidates import caches,
2. reads the current source bytes directly from disk,
3. derives a unique temporary module name from the resolved path and UUID,
4. creates and registers the module in sys.modules before source execution,
5. compiles and executes the current source directly without cached bytecode,
6. validates the loaded module,
7. removes the temporary module registration when validation is complete.

Registering the module before execution preserves Python 3.14 dataclass
compatibility.

The dependency main() callables are inspected but never invoked.

This gate never starts the Oracle service, creates a process, creates a thread,
places an order, moves funds, mutates a portfolio, or grants execution
authority.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib
from pathlib import Path
import sys
from types import MappingProxyType, ModuleType
from typing import Any, Mapping
from uuid import uuid4


SCHEMA_VERSION = "OLA-076"
ENGINE_ID = "OLA-076"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

REQUIRED_OLA075_SCHEMA_VERSION = "OLA-075"
REQUIRED_OLA075_ENGINE_ID = "OLA-075"

REQUIRED_OLA074_SCHEMA_VERSION = "OLA-074"
REQUIRED_OLA074_ENGINE_ID = "OLA-074"


class OracleContinuousDependencyError(RuntimeError):
    """Raised when an OLA-076 dependency fails closed validation."""


class OracleContinuousLaunchReadinessError(RuntimeError):
    """Raised when the final OLA-076 readiness contract is invalid."""


def _require_path(
    value: str | Path,
    field_name: str,
) -> Path:
    try:
        path = Path(value).expanduser().resolve(strict=False)
    except (TypeError, ValueError, OSError) as exc:
        raise OracleContinuousDependencyError(
            f"{field_name} must be a valid filesystem path"
        ) from exc

    if not path.exists():
        raise OracleContinuousDependencyError(
            f"{field_name} does not exist: {path}"
        )

    if not path.is_file():
        raise OracleContinuousDependencyError(
            f"{field_name} is not a file: {path}"
        )

    if path.suffix.lower() != ".py":
        raise OracleContinuousDependencyError(
            f"{field_name} must identify a Python source file: {path}"
        )

    return path


def _source_hash(source_bytes: bytes) -> str:
    return sha256(source_bytes).hexdigest()


def _unique_module_name(
    *,
    path: Path,
    source_hash: str,
) -> str:
    path_hash = sha256(
        str(path).encode("utf-8")
    ).hexdigest()[:16]

    return (
        "_ola076_dependency_"
        f"{path_hash}_"
        f"{source_hash[:16]}_"
        f"{uuid4().hex}"
    )


def _read_current_source(
    path: Path,
) -> tuple[bytes, str]:
    importlib.invalidate_caches()

    try:
        source_bytes = path.read_bytes()
    except OSError as exc:
        raise OracleContinuousDependencyError(
            f"could not read dependency source: {path}"
        ) from exc

    if not source_bytes:
        raise OracleContinuousDependencyError(
            f"dependency source is empty: {path}"
        )

    try:
        source_text = source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise OracleContinuousDependencyError(
            f"dependency source is not valid UTF-8: {path}"
        ) from exc

    return source_bytes, source_text


def _execute_fresh_source(
    path: str | Path,
) -> tuple[ModuleType, str, str]:
    """
    Execute the source currently present on disk.

    This intentionally does not use SourceFileLoader.exec_module() or the
    standard bytecode cache path. Reading, compiling, and executing the source
    directly guarantees that rewritten dependency content is observed
    immediately, even when file size and timestamp granularity are unchanged.
    """

    resolved_path = _require_path(
        path,
        "dependency_path",
    )

    source_bytes, source_text = _read_current_source(
        resolved_path
    )

    source_hash = _source_hash(source_bytes)

    module_name = _unique_module_name(
        path=resolved_path,
        source_hash=source_hash,
    )

    module = ModuleType(module_name)

    module.__file__ = str(resolved_path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None

    # Python 3.14 dataclasses inspect sys.modules while decorators execute.
    # The temporary module must therefore be registered before exec().
    sys.modules[module_name] = module

    try:
        try:
            code = compile(
                source_text,
                str(resolved_path),
                "exec",
                dont_inherit=True,
                optimize=0,
            )
        except (SyntaxError, ValueError, TypeError) as exc:
            raise OracleContinuousDependencyError(
                f"dependency source could not be compiled: {resolved_path}"
            ) from exc

        try:
            exec(
                code,
                module.__dict__,
                module.__dict__,
            )
        except OracleContinuousDependencyError:
            raise
        except BaseException as exc:
            raise OracleContinuousDependencyError(
                "dependency source raised during isolated loading: "
                f"{resolved_path}: {type(exc).__name__}: {exc}"
            ) from exc

        return module, module_name, source_hash

    except BaseException:
        sys.modules.pop(module_name, None)
        importlib.invalidate_caches()
        raise


def _require_exact_constant(
    module: ModuleType,
    *,
    field_name: str,
    expected_value: Any,
    dependency_label: str,
) -> None:
    actual_value = getattr(
        module,
        field_name,
        object(),
    )

    if actual_value != expected_value:
        raise OracleContinuousDependencyError(
            f"{dependency_label} has invalid {field_name}: "
            f"expected {expected_value!r}, got {actual_value!r}"
        )


def _validate_dependency_module(
    module: ModuleType,
    *,
    dependency_label: str,
    required_schema_version: str,
    required_engine_id: str,
) -> None:
    _require_exact_constant(
        module,
        field_name="SCHEMA_VERSION",
        expected_value=required_schema_version,
        dependency_label=dependency_label,
    )

    _require_exact_constant(
        module,
        field_name="ENGINE_ID",
        expected_value=required_engine_id,
        dependency_label=dependency_label,
    )

    main_callable = getattr(
        module,
        "main",
        None,
    )

    if not callable(main_callable):
        raise OracleContinuousDependencyError(
            f"{dependency_label} must expose callable main()"
        )

    _require_exact_constant(
        module,
        field_name="READ_ONLY",
        expected_value=True,
        dependency_label=dependency_label,
    )

    _require_exact_constant(
        module,
        field_name="EXECUTION_ALLOWED",
        expected_value=False,
        dependency_label=dependency_label,
    )

    prohibited_true_flags = (
        "EXECUTION_ADAPTER_RESOLVED",
        "EXECUTION_ADAPTER_INVOKED",
        "TRADE_AUTHORIZATION_ALLOWED",
        "ORDER_PLACEMENT_ALLOWED",
        "FUNDS_MOVED",
        "PORTFOLIO_MUTATED",
    )

    for field_name in prohibited_true_flags:
        actual_value = getattr(
            module,
            field_name,
            False,
        )

        if actual_value is not False:
            raise OracleContinuousDependencyError(
                f"{dependency_label} exposes prohibited authority "
                f"{field_name}={actual_value!r}"
            )


@dataclass(frozen=True, slots=True)
class OracleContinuousDependencyAttestation:
    schema_version: str
    engine_id: str
    dependency_label: str
    dependency_path: str
    dependency_source_hash: str
    temporary_module_name: str
    temporary_module_cleaned: bool
    current_disk_source_executed: bool
    bytecode_cache_bypassed: bool
    callable_main_verified: bool
    callable_main_invoked: bool
    read_only: bool
    execution_allowed: bool

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise OracleContinuousLaunchReadinessError(
                "dependency attestation schema invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleContinuousLaunchReadinessError(
                "dependency attestation engine invariant violated"
            )

        if not self.dependency_label:
            raise OracleContinuousLaunchReadinessError(
                "dependency label invariant violated"
            )

        if not self.dependency_path:
            raise OracleContinuousLaunchReadinessError(
                "dependency path invariant violated"
            )

        if len(self.dependency_source_hash) != 64:
            raise OracleContinuousLaunchReadinessError(
                "dependency source hash invariant violated"
            )

        if not self.temporary_module_name:
            raise OracleContinuousLaunchReadinessError(
                "temporary module name invariant violated"
            )

        if self.temporary_module_cleaned is not True:
            raise OracleContinuousLaunchReadinessError(
                "temporary module cleanup invariant violated"
            )

        if self.current_disk_source_executed is not True:
            raise OracleContinuousLaunchReadinessError(
                "current source execution invariant violated"
            )

        if self.bytecode_cache_bypassed is not True:
            raise OracleContinuousLaunchReadinessError(
                "bytecode bypass invariant violated"
            )

        if self.callable_main_verified is not True:
            raise OracleContinuousLaunchReadinessError(
                "callable main verification invariant violated"
            )

        if self.callable_main_invoked is not False:
            raise OracleContinuousLaunchReadinessError(
                "dependency main invocation invariant violated"
            )

        if self.read_only is not True:
            raise OracleContinuousLaunchReadinessError(
                "dependency read-only invariant violated"
            )

        if self.execution_allowed is not False:
            raise OracleContinuousLaunchReadinessError(
                "dependency execution invariant violated"
            )

    def to_dict(self) -> dict[str, Any]:
        self.assert_invariants()

        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "dependency_label": self.dependency_label,
            "dependency_path": self.dependency_path,
            "dependency_source_hash": self.dependency_source_hash,
            "temporary_module_name": self.temporary_module_name,
            "temporary_module_cleaned": self.temporary_module_cleaned,
            "current_disk_source_executed": (
                self.current_disk_source_executed
            ),
            "bytecode_cache_bypassed": self.bytecode_cache_bypassed,
            "callable_main_verified": self.callable_main_verified,
            "callable_main_invoked": self.callable_main_invoked,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
        }


def load_and_validate_dependency(
    *,
    dependency_path: str | Path,
    dependency_label: str,
    required_schema_version: str,
    required_engine_id: str,
) -> OracleContinuousDependencyAttestation:
    resolved_path = _require_path(
        dependency_path,
        f"{dependency_label}_path",
    )

    module: ModuleType | None = None
    module_name: str | None = None
    source_hash: str | None = None

    try:
        module, module_name, source_hash = _execute_fresh_source(
            resolved_path
        )

        _validate_dependency_module(
            module,
            dependency_label=dependency_label,
            required_schema_version=required_schema_version,
            required_engine_id=required_engine_id,
        )

    finally:
        if module_name is not None:
            sys.modules.pop(
                module_name,
                None,
            )

        importlib.invalidate_caches()

    if module_name is None or source_hash is None:
        raise OracleContinuousDependencyError(
            f"{dependency_label} did not complete isolated loading"
        )

    temporary_module_cleaned = (
        module_name not in sys.modules
    )

    if not temporary_module_cleaned:
        raise OracleContinuousDependencyError(
            f"{dependency_label} temporary module cleanup failed"
        )

    attestation = OracleContinuousDependencyAttestation(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        dependency_label=dependency_label,
        dependency_path=str(resolved_path),
        dependency_source_hash=source_hash,
        temporary_module_name=module_name,
        temporary_module_cleaned=True,
        current_disk_source_executed=True,
        bytecode_cache_bypassed=True,
        callable_main_verified=True,
        callable_main_invoked=False,
        read_only=True,
        execution_allowed=False,
    )

    attestation.assert_invariants()

    return attestation


@dataclass(frozen=True, slots=True)
class OracleContinuousOperatorLaunchReadinessRecord:
    schema_version: str
    engine_id: str
    readiness_status: str
    launch_ready: bool
    ola075_dependency: OracleContinuousDependencyAttestation
    ola074_dependency: OracleContinuousDependencyAttestation
    dependency_count: int
    unique_module_names_used: bool
    current_disk_sources_executed: bool
    bytecode_cache_bypassed: bool
    temporary_modules_cleaned: bool
    dependency_main_callables_verified: bool
    dependency_main_callables_invoked: bool
    real_continuous_service_started: bool
    process_created: bool
    thread_created: bool
    background_loop_started: bool
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise OracleContinuousLaunchReadinessError(
                "readiness schema invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleContinuousLaunchReadinessError(
                "readiness engine invariant violated"
            )

        if self.readiness_status != "ready":
            raise OracleContinuousLaunchReadinessError(
                "readiness status invariant violated"
            )

        if self.launch_ready is not True:
            raise OracleContinuousLaunchReadinessError(
                "launch readiness invariant violated"
            )

        self.ola075_dependency.assert_invariants()
        self.ola074_dependency.assert_invariants()

        if self.dependency_count != 2:
            raise OracleContinuousLaunchReadinessError(
                "dependency count invariant violated"
            )

        if self.unique_module_names_used is not True:
            raise OracleContinuousLaunchReadinessError(
                "unique module identity invariant violated"
            )

        if (
            self.ola075_dependency.temporary_module_name
            == self.ola074_dependency.temporary_module_name
        ):
            raise OracleContinuousLaunchReadinessError(
                "dependency module identities must be unique"
            )

        required_true_flags = (
            self.current_disk_sources_executed,
            self.bytecode_cache_bypassed,
            self.temporary_modules_cleaned,
            self.dependency_main_callables_verified,
        )

        if not all(value is True for value in required_true_flags):
            raise OracleContinuousLaunchReadinessError(
                "dependency freshness invariant violated"
            )

        required_false_flags = (
            self.dependency_main_callables_invoked,
            self.real_continuous_service_started,
            self.process_created,
            self.thread_created,
            self.background_loop_started,
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if not all(value is False for value in required_false_flags):
            raise OracleContinuousLaunchReadinessError(
                "read-only launch boundary invariant violated"
            )

        if self.read_only is not True:
            raise OracleContinuousLaunchReadinessError(
                "Oracle read-only invariant violated"
            )

    def to_dict(self) -> dict[str, Any]:
        self.assert_invariants()

        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "readiness_status": self.readiness_status,
            "launch_ready": self.launch_ready,
            "ola075_dependency": self.ola075_dependency.to_dict(),
            "ola074_dependency": self.ola074_dependency.to_dict(),
            "dependency_count": self.dependency_count,
            "unique_module_names_used": self.unique_module_names_used,
            "current_disk_sources_executed": (
                self.current_disk_sources_executed
            ),
            "bytecode_cache_bypassed": self.bytecode_cache_bypassed,
            "temporary_modules_cleaned": self.temporary_modules_cleaned,
            "dependency_main_callables_verified": (
                self.dependency_main_callables_verified
            ),
            "dependency_main_callables_invoked": (
                self.dependency_main_callables_invoked
            ),
            "real_continuous_service_started": (
                self.real_continuous_service_started
            ),
            "process_created": self.process_created,
            "thread_created": self.thread_created,
            "background_loop_started": self.background_loop_started,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": self.qseries_handoff_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": self.order_placement_allowed,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

    def to_canonical_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            self.to_dict()
        )


class OracleContinuousOperatorLaunchReadinessGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY
    execution_allowed = EXECUTION_ALLOWED

    def evaluate(
        self,
        *,
        ola075_path: str | Path,
        ola074_path: str | Path,
    ) -> OracleContinuousOperatorLaunchReadinessRecord:
        ola075_dependency = load_and_validate_dependency(
            dependency_path=ola075_path,
            dependency_label="OLA-075",
            required_schema_version=(
                REQUIRED_OLA075_SCHEMA_VERSION
            ),
            required_engine_id=(
                REQUIRED_OLA075_ENGINE_ID
            ),
        )

        ola074_dependency = load_and_validate_dependency(
            dependency_path=ola074_path,
            dependency_label="OLA-074",
            required_schema_version=(
                REQUIRED_OLA074_SCHEMA_VERSION
            ),
            required_engine_id=(
                REQUIRED_OLA074_ENGINE_ID
            ),
        )

        record = OracleContinuousOperatorLaunchReadinessRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            readiness_status="ready",
            launch_ready=True,
            ola075_dependency=ola075_dependency,
            ola074_dependency=ola074_dependency,
            dependency_count=2,
            unique_module_names_used=(
                ola075_dependency.temporary_module_name
                != ola074_dependency.temporary_module_name
            ),
            current_disk_sources_executed=True,
            bytecode_cache_bypassed=True,
            temporary_modules_cleaned=True,
            dependency_main_callables_verified=True,
            dependency_main_callables_invoked=False,
            real_continuous_service_started=False,
            process_created=False,
            thread_created=False,
            background_loop_started=False,
            read_only=True,
            execution_allowed=False,
            alerts_allowed=False,
            qseries_handoff_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        record.assert_invariants()

        return record

    def attest(
        self,
        *,
        ola075_path: str | Path,
        ola074_path: str | Path,
    ) -> OracleContinuousOperatorLaunchReadinessRecord:
        return self.evaluate(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

    def verify(
        self,
        *,
        ola075_path: str | Path,
        ola074_path: str | Path,
    ) -> OracleContinuousOperatorLaunchReadinessRecord:
        return self.evaluate(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )


def evaluate_continuous_operator_launch_readiness(
    *,
    ola075_path: str | Path,
    ola074_path: str | Path,
) -> OracleContinuousOperatorLaunchReadinessRecord:
    return OracleContinuousOperatorLaunchReadinessGate().evaluate(
        ola075_path=ola075_path,
        ola074_path=ola074_path,
    )


def attest_continuous_operator_launch_readiness(
    *,
    ola075_path: str | Path,
    ola074_path: str | Path,
) -> OracleContinuousOperatorLaunchReadinessRecord:
    return evaluate_continuous_operator_launch_readiness(
        ola075_path=ola075_path,
        ola074_path=ola074_path,
    )


# Backward-compatible descriptive aliases.
OracleContinuousOperatorReadinessGate = (
    OracleContinuousOperatorLaunchReadinessGate
)

OracleContinuousLaunchReadinessRecord = (
    OracleContinuousOperatorLaunchReadinessRecord
)
'''


TEST_SOURCE = r'''from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

from qseries_v2.oracle_intelligence.live_acquisition import (
    oracle_continuous_operator_launch_readiness_gate as ola076,
)


VALID_OLA075 = '''from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "OLA-075"
ENGINE_ID = "OLA-075"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


@dataclass(frozen=True, slots=True)
class OLA075Record:
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False


def main() -> int:
    raise AssertionError(
        "OLA-075 main() must never be invoked by OLA-076"
    )
'''


VALID_OLA074 = '''from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "OLA-074"
ENGINE_ID = "OLA-074"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


@dataclass(frozen=True, slots=True)
class OLA074Record:
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False


def main() -> int:
    raise AssertionError(
        "OLA-074 main() must never be invoked by OLA-076"
    )
'''


def write_source(
    path: Path,
    source: str,
) -> None:
    path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    # Explicitly update the timestamp where the filesystem permits it.
    # The loader must still work correctly even if timestamp granularity
    # causes consecutive writes to appear identical.
    os.utime(
        path,
        None,
    )


def expect_dependency_error(
    label: str,
    callable_under_test,
) -> None:
    try:
        callable_under_test()
    except ola076.OracleContinuousDependencyError:
        return

    raise AssertionError(
        f"{label} expected OracleContinuousDependencyError"
    )


def temporary_ola076_modules() -> set[str]:
    return {
        name
        for name in sys.modules
        if name.startswith("_ola076_dependency_")
    }


def main() -> int:
    assert ola076.SCHEMA_VERSION == "OLA-076"
    assert ola076.ENGINE_ID == "OLA-076"

    assert ola076.READ_ONLY is True
    assert ola076.EXECUTION_ALLOWED is False
    assert ola076.ALERTS_ALLOWED is False
    assert ola076.QSERIES_HANDOFF_ALLOWED is False
    assert ola076.EXECUTION_ADAPTER_RESOLVED is False
    assert ola076.EXECUTION_ADAPTER_INVOKED is False
    assert ola076.TRADE_AUTHORIZATION_ALLOWED is False
    assert ola076.ORDER_PLACEMENT_ALLOWED is False
    assert ola076.FUNDS_MOVED is False
    assert ola076.PORTFOLIO_MUTATED is False

    gate = ola076.OracleContinuousOperatorLaunchReadinessGate()

    assert gate.read_only is True
    assert gate.execution_allowed is False

    baseline_temporary_modules = temporary_ola076_modules()

    service_start_calls: list[str] = []

    def forbidden_process_start(*args, **kwargs):
        service_start_calls.append("process")
        raise AssertionError(
            "OLA-076 must not create a process"
        )

    def forbidden_thread_start(*args, **kwargs):
        service_start_calls.append("thread")
        raise AssertionError(
            "OLA-076 must not start a thread"
        )

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)

        ola075_path = root / "ola075_dependency.py"
        ola074_path = root / "ola074_dependency.py"

        write_source(
            ola075_path,
            VALID_OLA075,
        )

        write_source(
            ola074_path,
            VALID_OLA074,
        )

        with (
            patch(
                "subprocess.Popen",
                side_effect=forbidden_process_start,
            ),
            patch(
                "threading.Thread.start",
                side_effect=forbidden_thread_start,
            ),
        ):
            first_record = gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            )

        first_record.assert_invariants()

        assert first_record.schema_version == "OLA-076"
        assert first_record.engine_id == "OLA-076"
        assert first_record.readiness_status == "ready"
        assert first_record.launch_ready is True
        assert first_record.dependency_count == 2

        assert first_record.ola075_dependency.dependency_label == "OLA-075"
        assert first_record.ola074_dependency.dependency_label == "OLA-074"

        assert first_record.unique_module_names_used is True
        assert first_record.current_disk_sources_executed is True
        assert first_record.bytecode_cache_bypassed is True
        assert first_record.temporary_modules_cleaned is True

        assert first_record.dependency_main_callables_verified is True
        assert first_record.dependency_main_callables_invoked is False
        assert first_record.real_continuous_service_started is False
        assert first_record.process_created is False
        assert first_record.thread_created is False
        assert first_record.background_loop_started is False

        assert first_record.read_only is True
        assert first_record.execution_allowed is False
        assert first_record.alerts_allowed is False
        assert first_record.qseries_handoff_allowed is False
        assert first_record.execution_adapter_resolved is False
        assert first_record.execution_adapter_invoked is False
        assert first_record.trade_authorization_allowed is False
        assert first_record.order_placement_allowed is False
        assert first_record.funds_moved is False
        assert first_record.portfolio_mutated is False

        assert service_start_calls == []

        assert (
            first_record.ola075_dependency.temporary_module_name
            not in sys.modules
        )

        assert (
            first_record.ola074_dependency.temporary_module_name
            not in sys.modules
        )

        first_ola075_module_name = (
            first_record.ola075_dependency.temporary_module_name
        )

        first_ola074_module_name = (
            first_record.ola074_dependency.temporary_module_name
        )

        first_ola075_hash = (
            first_record.ola075_dependency.dependency_source_hash
        )

        first_ola074_hash = (
            first_record.ola074_dependency.dependency_source_hash
        )

        # Rewrite OLA-075 immediately. No sleep is used because correctness
        # must not depend on filesystem timestamp resolution.
        invalid_ola075_schema = VALID_OLA075.replace(
            'SCHEMA_VERSION = "OLA-075"',
            'SCHEMA_VERSION = "OLA-999"',
            1,
        )

        write_source(
            ola075_path,
            invalid_ola075_schema,
        )

        expect_dependency_error(
            "Incorrect OLA-075 dependency schema",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # Restore OLA-075 and prove a new isolated module is used.
        write_source(
            ola075_path,
            VALID_OLA075,
        )

        second_record = gate.evaluate(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

        second_record.assert_invariants()

        assert (
            second_record.ola075_dependency.temporary_module_name
            != first_ola075_module_name
        )

        assert (
            second_record.ola074_dependency.temporary_module_name
            != first_ola074_module_name
        )

        assert (
            second_record.ola075_dependency.dependency_source_hash
            == first_ola075_hash
        )

        assert (
            second_record.ola074_dependency.dependency_source_hash
            == first_ola074_hash
        )

        assert temporary_ola076_modules() == baseline_temporary_modules

        # Rewrite OLA-074 immediately with an invalid engine identity.
        invalid_ola074_engine = VALID_OLA074.replace(
            'ENGINE_ID = "OLA-074"',
            'ENGINE_ID = "OLA-999"',
            1,
        )

        write_source(
            ola074_path,
            invalid_ola074_engine,
        )

        expect_dependency_error(
            "Incorrect OLA-074 dependency engine",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # Restore OLA-074.
        write_source(
            ola074_path,
            VALID_OLA074,
        )

        third_record = ola076.evaluate_continuous_operator_launch_readiness(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

        third_record.assert_invariants()

        assert (
            third_record.ola075_dependency.temporary_module_name
            != second_record.ola075_dependency.temporary_module_name
        )

        assert (
            third_record.ola074_dependency.temporary_module_name
            != second_record.ola074_dependency.temporary_module_name
        )

        # Missing callable main() must fail closed.
        missing_main_ola075 = VALID_OLA075.replace(
            '''def main() -> int:
    raise AssertionError(
        "OLA-075 main() must never be invoked by OLA-076"
    )
''',
            '''main = None
''',
            1,
        )

        write_source(
            ola075_path,
            missing_main_ola075,
        )

        expect_dependency_error(
            "Missing OLA-075 callable main()",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # Execution-enabled dependency must fail closed.
        execution_enabled_ola075 = VALID_OLA075.replace(
            "EXECUTION_ALLOWED = False",
            "EXECUTION_ALLOWED = True",
            1,
        )

        write_source(
            ola075_path,
            execution_enabled_ola075,
        )

        expect_dependency_error(
            "Execution-enabled OLA-075 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # The same fail-closed execution rule applies to OLA-074.
        write_source(
            ola075_path,
            VALID_OLA075,
        )

        execution_enabled_ola074 = VALID_OLA074.replace(
            "EXECUTION_ALLOWED = False",
            "EXECUTION_ALLOWED = True",
            1,
        )

        write_source(
            ola074_path,
            execution_enabled_ola074,
        )

        expect_dependency_error(
            "Execution-enabled OLA-074 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # Prohibited authority flags must also fail closed.
        write_source(
            ola074_path,
            VALID_OLA074.replace(
                "ORDER_PLACEMENT_ALLOWED = False",
                "ORDER_PLACEMENT_ALLOWED = True",
                1,
            ),
        )

        expect_dependency_error(
            "Order-enabled OLA-074 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        # Final valid run.
        write_source(
            ola074_path,
            VALID_OLA074,
        )

        final_record = gate.attest(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

        final_payload = final_record.to_dict()

        assert final_payload["launch_ready"] is True
        assert final_payload["read_only"] is True
        assert final_payload["execution_allowed"] is False
        assert final_payload["real_continuous_service_started"] is False

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

    print(
        "[PASS] OLA-076 Oracle Continuous Operator "
        "Launch Readiness Gate Correction V3"
    )

    print({
        "schema_version": "OLA-076",
        "engine_id": "OLA-076",
        "status": "passed",
        "python_314_dataclass_module_registration_preserved": True,
        "unique_module_name_per_dynamic_load": True,
        "unique_name_includes_path_hash_source_hash_and_uuid": True,
        "current_disk_source_executed_every_time": True,
        "standard_bytecode_cache_bypassed": True,
        "import_caches_invalidated": True,
        "temporary_module_registration_cleaned": True,
        "valid_ola075_dependency_passed": True,
        "valid_ola074_dependency_passed": True,
        "rewritten_ola075_invalid_schema_detected_immediately": True,
        "rewritten_ola074_invalid_engine_detected_immediately": True,
        "missing_callable_main_rejected": True,
        "execution_enabled_dependency_rejected": True,
        "prohibited_authority_flag_rejected": True,
        "stale_module_reuse_prevented": True,
        "stale_bytecode_reuse_prevented": True,
        "dependency_main_not_invoked": True,
        "real_continuous_service_started": False,
        "process_created": False,
        "thread_created": False,
        "background_loop_started": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-076 PRODUCTION CORRECTION V3")
    print(" FRESH SOURCE DYNAMIC DEPENDENCY LOADING")
    print(" PYTHON 3.14 DATACLASS COMPATIBILITY")
    print("========================================")

    write_full_replacement(
        PRODUCTION_PATH,
        PRODUCTION_SOURCE,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    compile(
        PRODUCTION_PATH.read_text(
            encoding="utf-8",
        ),
        str(PRODUCTION_PATH),
        "exec",
    )

    compile(
        TEST_PATH.read_text(
            encoding="utf-8",
        ),
        str(TEST_PATH),
        "exec",
    )

    print("[OK] Complete OLA-076 production module replaced")
    print("[OK] Complete OLA-076 regression test replaced")
    print("[OK] Unique dependency module identity installed")
    print("[OK] Direct current-source compilation installed")
    print("[OK] Standard bytecode cache reuse bypassed")
    print("[OK] Import cache invalidation installed")
    print("[OK] Python 3.14 sys.modules registration preserved")
    print("[OK] Temporary module cleanup installed")
    print("[OK] Dependency main() invocation prohibited")
    print("[OK] Oracle read-only boundary preserved")

    print(
        "\n[DONE] OLA-076 production correction V3 installed"
    )

    print("\nRun:")
    print(
        "py test_ola_076_"
        "oracle_continuous_operator_launch_readiness_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())