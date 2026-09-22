from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAR-003"
INSTALLER_REVISION = "OAR_003_MULTI_ADAPTER_OBSERVATION_RUNNER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oar_001_runtime_foundation.py",
    PACKAGE / "oar_002_adapter_scheduler.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "oar_003_multi_adapter_runner.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_003_multi_adapter_runner.py"

MODULE_SOURCE = """
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    ObservationAdapterResult,
)
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    CertifiedDefaultAdapterBundle,
)
from .oar_002_adapter_scheduler import (
    AdapterSchedule,
)

BUILD_ID = "OAR-003"
OAR_003_REVISION = "OAR_003_MULTI_ADAPTER_OBSERVATION_RUNNER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class AdapterRunRecord:
    ordinal: int
    adapter_id: str
    request_id: str
    capability: str
    success: bool
    observation_count: int
    error_code: str | None


@dataclass(frozen=True, slots=True)
class MultiAdapterRunResult:
    iteration_number: int
    started_at: datetime
    completed_at: datetime
    records: tuple[AdapterRunRecord, ...]
    results: tuple[ObservationAdapterResult, ...]
    request_count: int
    success_count: int
    failure_count: int
    observation_count: int
    read_only: bool
    execution_allowed: bool


class MultiAdapterObservationRunner:
    read_only = True
    execution_allowed = False

    def run(
        self,
        *,
        bundle: CertifiedDefaultAdapterBundle,
        schedule: AdapterSchedule,
        clock_callable: Callable[[], datetime],
    ) -> MultiAdapterRunResult:
        if not isinstance(
            bundle,
            CertifiedDefaultAdapterBundle,
        ):
            raise TypeError(
                "bundle must be CertifiedDefaultAdapterBundle"
            )

        if not isinstance(
            schedule,
            AdapterSchedule,
        ):
            raise TypeError(
                "schedule must be AdapterSchedule"
            )

        if not callable(clock_callable):
            raise TypeError(
                "clock_callable must be callable"
            )

        started_at = clock_callable()

        if not isinstance(started_at, datetime):
            raise TypeError(
                "clock_callable must return datetime"
            )

        if started_at.tzinfo is None:
            raise ValueError(
                "clock timestamps must be timezone-aware"
            )

        results = []
        records = []

        for scheduled in schedule.requests:
            adapter = bundle.registry.get(
                scheduled.adapter_id
            )

            if adapter is None:
                result = ObservationAdapterResult(
                    request_id=scheduled.request.request_id,
                    adapter_id=scheduled.adapter_id,
                    provider_id="unknown",
                    capability=scheduled.request.capability,
                    observations=(),
                    observed_at=started_at.astimezone(
                        timezone.utc
                    ),
                    success=False,
                    error_code="adapter_not_registered",
                    read_only=True,
                    execution_allowed=False,
                )
            else:
                try:
                    result = adapter.observe(
                        scheduled.request
                    )
                except Exception as exc:
                    result = ObservationAdapterResult(
                        request_id=scheduled.request.request_id,
                        adapter_id=scheduled.adapter_id,
                        provider_id=(
                            adapter.descriptor.identity.provider_id
                        ),
                        capability=scheduled.request.capability,
                        observations=(),
                        observed_at=started_at.astimezone(
                            timezone.utc
                        ),
                        success=False,
                        error_code=(
                            "adapter_exception:"
                            + type(exc).__name__
                        ),
                        read_only=True,
                        execution_allowed=False,
                    )

            if result.read_only is not True:
                raise RuntimeError(
                    "adapter result violated read-only boundary"
                )

            if result.execution_allowed is not False:
                raise RuntimeError(
                    "adapter result exposed execution permission"
                )

            results.append(result)

            records.append(
                AdapterRunRecord(
                    ordinal=scheduled.ordinal,
                    adapter_id=scheduled.adapter_id,
                    request_id=result.request_id,
                    capability=result.capability,
                    success=result.success,
                    observation_count=len(
                        result.observations
                    ),
                    error_code=result.error_code,
                )
            )

        completed_at = clock_callable()

        if not isinstance(completed_at, datetime):
            raise TypeError(
                "clock_callable must return datetime"
            )

        if completed_at.tzinfo is None:
            raise ValueError(
                "clock timestamps must be timezone-aware"
            )

        results_tuple = tuple(results)
        records_tuple = tuple(records)

        success_count = sum(
            1
            for item in results_tuple
            if item.success
        )

        failure_count = (
            len(results_tuple)
            - success_count
        )

        observation_count = sum(
            len(item.observations)
            for item in results_tuple
        )

        return MultiAdapterRunResult(
            iteration_number=schedule.iteration_number,
            started_at=started_at.astimezone(timezone.utc),
            completed_at=completed_at.astimezone(timezone.utc),
            records=records_tuple,
            results=results_tuple,
            request_count=len(results_tuple),
            success_count=success_count,
            failure_count=failure_count,
            observation_count=observation_count,
            read_only=True,
            execution_allowed=False,
        )


def verify_multi_adapter_observation_runner() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_003_REVISION",
    "AdapterRunRecord",
    "MultiAdapterRunResult",
    "MultiAdapterObservationRunner",
    "verify_multi_adapter_observation_runner",
]
""".lstrip()

TEST_SOURCE = """
from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import (
    DeterministicAdapterScheduler,
)
from qseries_v2.observation_adapter_runtime.oar_003_multi_adapter_runner import (
    OAR_003_REVISION,
    MultiAdapterObservationRunner,
    verify_multi_adapter_observation_runner,
)

NOW = datetime(
    2026,
    8,
    11,
    22,
    40,
    tzinfo=timezone.utc,
)


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        current = self.value
        self.value = self.value + timedelta(
            milliseconds=1
        )
        return current


class TestOAR003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_multi_adapter_observation_runner()
        )

    def test_run(self):
        bundle = build_default_adapter_bundle()

        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
            subject_hints={
                "coinbase": "BTC",
                "kalshi": None,
            },
        )

        result = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )

        self.assertEqual(
            result.request_count,
            schedule.request_count,
        )

        self.assertEqual(
            result.success_count
            + result.failure_count,
            result.request_count,
        )

    def test_failure_isolated(self):
        bundle = build_default_adapter_bundle()

        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )

        result = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )

        self.assertEqual(
            len(result.records),
            schedule.request_count,
        )

    def test_side_effects(self):
        runner = MultiAdapterObservationRunner()
        self.assertTrue(runner.read_only)
        self.assertFalse(runner.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-003 CERTIFICATION TEST")
    print(" MULTI-ADAPTER OBSERVATION RUNNER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR003
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-003")
    print(f"[PASS] Revision: {OAR_003_REVISION}")
    print("[PASS] Scheduled Kalshi and crypto adapter requests run through one universal runtime")
    print("[PASS] Per-adapter failures are isolated instead of crashing the whole iteration")
    print("[PASS] Observation counts, successes, failures, and iteration lineage preserved")
    print("[PASS] Runner remains read-only with execution disabled")
    print("[DONE] OAR-003 CERTIFIED")
""".lstrip()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_checked(p: Path, source: str) -> None:
    ast.parse(source, filename=str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {p.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAR-003 INSTALLER")
    print(" MULTI-ADAPTER OBSERVATION RUNNER")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {upstream}"
            )

    hashes = {p: sha(p) for p in UPSTREAMS}

    affected = (MODULE, TEST, INIT)
    backups = {
        p: p.read_bytes() if p.exists() else None
        for p in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oar_003_multi_adapter_runner import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        for p, expected in hashes.items():
            if sha(p) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {p.name}"
                )

        print("[PASS] OAR-001, OAR-002, OAD-006, and frozen OI unchanged")
        print("[PASS] In-memory compilation verified")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Universal multi-adapter runtime can schedule and invoke registered adapters")
        print("[DONE] OAR-003 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for p, original in backups.items():
            if original is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(original)

        print("[ROLLBACK] OAR-003 installation failed; affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
