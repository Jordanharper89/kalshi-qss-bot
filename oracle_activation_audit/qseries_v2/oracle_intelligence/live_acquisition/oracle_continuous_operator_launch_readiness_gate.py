"""
OLA-076
Oracle Continuous Operator Launch Readiness Gate
Production Correction V3

Fresh-source dependency loading correction.

Every dependency load:

1. invalidates Python import caches,
2. reads the source currently present on disk,
3. derives a unique temporary module name from the resolved path,
   source hash, and UUID,
4. registers that module in sys.modules before execution for Python 3.14
   dataclass compatibility,
5. compiles and executes the current source directly,
6. bypasses stale .pyc and import-loader bytecode reuse,
7. validates the dependency contract,
8. removes the temporary module from sys.modules.

Dependency main() callables are validated but never invoked.

This readiness gate never starts the continuous Oracle service and never
grants execution authority. Oracle remains permanently read-only.
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
    """Raised when the OLA-076 readiness contract is invalid."""


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


def _execute_fresh_source(
    path: str | Path,
) -> tuple[ModuleType, str, str]:
    """
    Execute the exact source currently on disk.

    Direct read, compile, and exec are deliberate. They prevent a rewritten
    dependency from being replaced by an earlier module or timestamp-valid
    bytecode cache entry.
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

    # Required by Python 3.14 dataclass processing.
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
    missing = object()

    actual_value = getattr(
        module,
        field_name,
        missing,
    )

    if actual_value is missing:
        raise OracleContinuousDependencyError(
            f"{dependency_label} is missing required {field_name}"
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

    if module_name in sys.modules:
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


OracleContinuousOperatorReadinessGate = (
    OracleContinuousOperatorLaunchReadinessGate
)

OracleContinuousLaunchReadinessRecord = (
    OracleContinuousOperatorLaunchReadinessRecord
)
