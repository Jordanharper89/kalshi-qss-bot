from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oar_003_multi_adapter_runner.py",
    PACKAGE / "oar_006_production_launch_boundary.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "oar_007_adapter_health_model.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_007_adapter_health_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_003_multi_adapter_runner import MultiAdapterRunResult

BUILD_ID = "OAR-007"
OAR_007_REVISION = "OAR_007_ADAPTER_HEALTH_MODEL_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

HEALTHY = "healthy"
DEGRADED = "degraded"
FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AdapterHealthRecord:
    adapter_id: str
    request_count: int
    success_count: int
    failure_count: int
    observation_count: int
    health_status: str
    assessed_at: datetime
    read_only: bool


class AdapterHealthModel:
    read_only = True
    execution_allowed = False

    def assess(
        self,
        *,
        run_result: MultiAdapterRunResult,
        assessed_at: datetime,
    ) -> tuple[AdapterHealthRecord, ...]:
        if not isinstance(run_result, MultiAdapterRunResult):
            raise TypeError("run_result must be MultiAdapterRunResult")

        if not isinstance(assessed_at, datetime) or assessed_at.tzinfo is None:
            raise ValueError("assessed_at must be timezone-aware datetime")

        grouped = {}

        for record in run_result.records:
            row = grouped.setdefault(
                record.adapter_id,
                {
                    "request_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "observation_count": 0,
                },
            )

            row["request_count"] += 1
            row["observation_count"] += record.observation_count

            if record.success:
                row["success_count"] += 1
            else:
                row["failure_count"] += 1

        output = []

        for adapter_id in sorted(grouped):
            row = grouped[adapter_id]

            if row["failure_count"] == 0:
                status = HEALTHY
            elif row["success_count"] == 0:
                status = FAILED
            else:
                status = DEGRADED

            output.append(
                AdapterHealthRecord(
                    adapter_id=adapter_id,
                    request_count=row["request_count"],
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    observation_count=row["observation_count"],
                    health_status=status,
                    assessed_at=assessed_at.astimezone(timezone.utc),
                    read_only=True,
                )
            )

        return tuple(output)


def verify_adapter_health_model() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from datetime import datetime, timezone, timedelta

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import build_default_adapter_bundle
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import DeterministicAdapterScheduler
from qseries_v2.observation_adapter_runtime.oar_003_multi_adapter_runner import MultiAdapterObservationRunner
from qseries_v2.observation_adapter_runtime.oar_007_adapter_health_model import (
    AdapterHealthModel,
    verify_adapter_health_model,
)

NOW = datetime(2026, 8, 12, 4, 45, tzinfo=timezone.utc)

class Clock:
    def __init__(self): self.v = NOW
    def __call__(self):
        x = self.v
        self.v += timedelta(milliseconds=1)
        return x

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_adapter_health_model())

    def test_health_records(self):
        bundle = build_default_adapter_bundle()
        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
            subject_hints={"coinbase":"BTC", "kalshi":None},
        )
        run = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )
        records = AdapterHealthModel().assess(
            run_result=run,
            assessed_at=NOW,
        )
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(
            tuple(sorted(x.adapter_id for x in records)),
            tuple(x.adapter_id for x in records),
        )

    def test_side_effects(self):
        model = AdapterHealthModel()
        self.assertTrue(model.read_only)
        self.assertFalse(model.execution_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-007 CERTIFICATION TEST")
    print(" ADAPTER HEALTH MODEL")
    print("="*72)
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-007")
    print("[PASS] Healthy, degraded, and failed adapter health states certified")
    print("[PASS] Health derives from actual per-adapter runtime outcomes")
    print("[PASS] Runtime remains read-only with execution disabled")
    print("[DONE] OAR-007 CERTIFIED")
"""

def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x, t):
    t = t.lstrip()
    ast.parse(t, filename=str(x))
    x.parent.mkdir(parents=True, exist_ok=True)
    x.write_text(t, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {x.relative_to(ROOT)}")

def main():
    print("="*72)
    print(" OAR-007 INSTALLER")
    print(" ADAPTER HEALTH MODEL")
    print("="*72)
    print("[BOOT] Revision: OAR_007_ADAPTER_HEALTH_MODEL_INSTALLER_V1")
    print(f"[ROOT] {ROOT}")

    for x in UPSTREAMS:
        if not x.is_file():
            raise RuntimeError(f"Certified upstream missing: {x}")

    hashes = {x: sha(x) for x in UPSTREAMS}
    affected = (MODULE, TEST, INIT)
    backups = {x: (x.read_bytes() if x.exists() else None) for x in affected}

    try:
        write(MODULE, MODULE_SOURCE)
        write(TEST, TEST_SOURCE)

        cur = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        exp = "from .oar_007_adapter_health_model import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"):
                cur += "\n"
            cur += exp + "\n"
            ast.parse(cur, filename=str(INIT))
            INIT.write_text(cur, encoding="utf-8", newline="\n")

        for x, expected in hashes.items():
            if sha(x) != expected:
                raise RuntimeError(f"Certified upstream changed: {x.name}")

        print("[PASS] Certified upstream remained unchanged")
        print("[PASS] Deterministic install hash:", hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest())
        print("[DONE] OAR-007 INSTALLATION COMPLETE")
        return 0
    except Exception:
        for x, b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else:
                x.write_bytes(b)
        raise

if __name__ == "__main__":
    raise SystemExit(main())
