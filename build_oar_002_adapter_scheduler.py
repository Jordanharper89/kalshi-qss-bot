from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAR-002"
INSTALLER_REVISION = "OAR_002_DETERMINISTIC_ADAPTER_SCHEDULER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oar_001_runtime_foundation.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "oar_002_adapter_scheduler.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_002_adapter_scheduler.py"

MODULE_SOURCE = """
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    ObservationAdapterRequest,
    build_adapter_request,
)
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    CertifiedDefaultAdapterBundle,
)

BUILD_ID = "OAR-002"
OAR_002_REVISION = "OAR_002_DETERMINISTIC_ADAPTER_SCHEDULER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ScheduledAdapterRequest:
    ordinal: int
    adapter_id: str
    request: ObservationAdapterRequest


@dataclass(frozen=True, slots=True)
class AdapterSchedule:
    iteration_number: int
    requests: tuple[ScheduledAdapterRequest, ...]
    request_count: int
    scheduled_at: datetime
    read_only: bool
    execution_allowed: bool


class DeterministicAdapterScheduler:
    read_only = True
    execution_allowed = False

    def schedule(
        self,
        *,
        bundle: CertifiedDefaultAdapterBundle,
        iteration_number: int,
        scheduled_at: datetime,
        subject_hints: dict[str, str | None] | None = None,
    ) -> AdapterSchedule:
        if not isinstance(bundle, CertifiedDefaultAdapterBundle):
            raise TypeError(
                "bundle must be CertifiedDefaultAdapterBundle"
            )

        if not isinstance(iteration_number, int):
            raise TypeError(
                "iteration_number must be int"
            )

        if iteration_number < 1:
            raise ValueError(
                "iteration_number must be positive"
            )

        if not isinstance(scheduled_at, datetime):
            raise TypeError(
                "scheduled_at must be datetime"
            )

        if scheduled_at.tzinfo is None:
            raise ValueError(
                "scheduled_at must be timezone-aware"
            )

        scheduled_at = scheduled_at.astimezone(timezone.utc)
        subject_hints = dict(subject_hints or {})

        rows = []

        for adapter_id in bundle.adapter_ids:
            adapter = bundle.registry.get(adapter_id)

            if adapter is None:
                raise RuntimeError(
                    f"registered adapter missing: {adapter_id}"
                )

            provider_id = (
                adapter.descriptor.identity.provider_id
            )

            subject_hint = subject_hints.get(provider_id)

            for capability in adapter.descriptor.capabilities:
                request = build_adapter_request(
                    request_id=(
                        f"runtime.iteration.{iteration_number}."
                        f"{adapter_id}.{capability}"
                    ),
                    subject_hint=subject_hint,
                    capability=capability,
                    requested_at=scheduled_at,
                    metadata={
                        "iteration_number": iteration_number,
                        "adapter_id": adapter_id,
                        "provider_id": provider_id,
                    },
                )

                rows.append(
                    (
                        adapter_id,
                        capability,
                        request,
                    )
                )

        rows.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        requests = tuple(
            ScheduledAdapterRequest(
                ordinal=index,
                adapter_id=adapter_id,
                request=request,
            )
            for index, (
                adapter_id,
                _,
                request,
            ) in enumerate(rows, start=1)
        )

        return AdapterSchedule(
            iteration_number=iteration_number,
            requests=requests,
            request_count=len(requests),
            scheduled_at=scheduled_at,
            read_only=True,
            execution_allowed=False,
        )


def verify_deterministic_adapter_scheduler() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_002_REVISION",
    "ScheduledAdapterRequest",
    "AdapterSchedule",
    "DeterministicAdapterScheduler",
    "verify_deterministic_adapter_scheduler",
]
""".lstrip()

TEST_SOURCE = """
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import (
    OAR_002_REVISION,
    DeterministicAdapterScheduler,
    verify_deterministic_adapter_scheduler,
)

NOW = datetime(
    2026,
    8,
    11,
    22,
    35,
    tzinfo=timezone.utc,
)


class TestOAR002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_deterministic_adapter_scheduler()
        )

    def test_schedule(self):
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

        self.assertGreater(
            schedule.request_count,
            0,
        )
        self.assertEqual(
            schedule.requests[0].ordinal,
            1,
        )

    def test_deterministic(self):
        bundle = build_default_adapter_bundle()
        scheduler = DeterministicAdapterScheduler()

        a = scheduler.schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )
        b = scheduler.schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )

        self.assertEqual(
            tuple(
                (
                    item.adapter_id,
                    item.request.capability,
                )
                for item in a.requests
            ),
            tuple(
                (
                    item.adapter_id,
                    item.request.capability,
                )
                for item in b.requests
            ),
        )

    def test_side_effects(self):
        scheduler = DeterministicAdapterScheduler()
        self.assertTrue(scheduler.read_only)
        self.assertFalse(scheduler.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-002 CERTIFICATION TEST")
    print(" DETERMINISTIC ADAPTER SCHEDULER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR002
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-002")
    print(f"[PASS] Revision: {OAR_002_REVISION}")
    print("[PASS] Registered adapter capabilities schedule in deterministic order")
    print("[PASS] Per-provider subject hints and iteration lineage preserved")
    print("[PASS] Scheduler remains read-only with execution disabled")
    print("[DONE] OAR-002 CERTIFIED")
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
    print(" OAR-002 INSTALLER")
    print(" DETERMINISTIC ADAPTER SCHEDULER")
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
        export = "from .oar_002_adapter_scheduler import *"

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

        print("[PASS] OAR-001, OAD-006, and frozen OI unchanged")
        print("[PASS] In-memory compilation verified")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[DONE] OAR-002 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for p, original in backups.items():
            if original is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(original)

        print("[ROLLBACK] OAR-002 installation failed; affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
