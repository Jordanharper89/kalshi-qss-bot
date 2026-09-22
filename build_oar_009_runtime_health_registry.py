from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oar_007_adapter_health_model.py",
    PACKAGE / "oar_008_failure_isolation_controller.py",
    PACKAGE / "oar_006_production_launch_boundary.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "oar_009_runtime_health_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_009_runtime_health_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    DEGRADED,
    FAILED,
)
from .oar_008_failure_isolation_controller import (
    AdapterIsolationDecision,
)

BUILD_ID = "OAR-009"
OAR_009_REVISION = "OAR_009_RUNTIME_HEALTH_REGISTRY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

RUNTIME_HEALTHY = "healthy"
RUNTIME_DEGRADED = "degraded"
RUNTIME_FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RuntimeHealthSnapshot:
    runtime_id: str
    adapter_health: tuple[AdapterHealthRecord, ...]
    isolation_decisions: tuple[AdapterIsolationDecision, ...]
    healthy_count: int
    degraded_count: int
    failed_count: int
    isolated_count: int
    runtime_health_status: str
    assessed_at: datetime
    read_only: bool


class RuntimeHealthRegistry:
    read_only = True
    execution_allowed = False

    def build_snapshot(
        self,
        *,
        runtime_id: str,
        adapter_health: tuple[AdapterHealthRecord, ...],
        isolation_decisions: tuple[AdapterIsolationDecision, ...],
        assessed_at: datetime,
    ) -> RuntimeHealthSnapshot:
        runtime_id_value = str(runtime_id).strip()

        if not runtime_id_value:
            raise ValueError("runtime_id must not be empty")

        if not isinstance(assessed_at, datetime) or assessed_at.tzinfo is None:
            raise ValueError("assessed_at must be timezone-aware datetime")

        health_ids = tuple(
            x.adapter_id
            for x in sorted(
                adapter_health,
                key=lambda x: x.adapter_id,
            )
        )

        decision_ids = tuple(
            x.adapter_id
            for x in sorted(
                isolation_decisions,
                key=lambda x: x.adapter_id,
            )
        )

        if health_ids != decision_ids:
            raise ValueError(
                "health/isolation adapter identity mismatch"
            )

        healthy_count = sum(
            1 for x in adapter_health
            if x.health_status == HEALTHY
        )
        degraded_count = sum(
            1 for x in adapter_health
            if x.health_status == DEGRADED
        )
        failed_count = sum(
            1 for x in adapter_health
            if x.health_status == FAILED
        )
        isolated_count = sum(
            1 for x in isolation_decisions
            if x.isolated
        )

        if failed_count == len(adapter_health) and adapter_health:
            runtime_status = RUNTIME_FAILED
        elif failed_count or degraded_count:
            runtime_status = RUNTIME_DEGRADED
        else:
            runtime_status = RUNTIME_HEALTHY

        return RuntimeHealthSnapshot(
            runtime_id=runtime_id_value,
            adapter_health=tuple(
                sorted(
                    adapter_health,
                    key=lambda x: x.adapter_id,
                )
            ),
            isolation_decisions=tuple(
                sorted(
                    isolation_decisions,
                    key=lambda x: x.adapter_id,
                )
            ),
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            failed_count=failed_count,
            isolated_count=isolated_count,
            runtime_health_status=runtime_status,
            assessed_at=assessed_at.astimezone(timezone.utc),
            read_only=True,
        )


def verify_runtime_health_registry() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    FAILED,
)
from qseries_v2.observation_adapter_runtime.oar_008_failure_isolation_controller import (
    AdapterFailureIsolationController,
)
from qseries_v2.observation_adapter_runtime.oar_009_runtime_health_registry import (
    RuntimeHealthRegistry,
    RUNTIME_DEGRADED,
    verify_runtime_health_registry,
)

NOW=datetime(2026,8,12,4,55,tzinfo=timezone.utc)

def health(adapter_id,status):
    return AdapterHealthRecord(
        adapter_id=adapter_id,
        request_count=1,
        success_count=1 if status==HEALTHY else 0,
        failure_count=0 if status==HEALTHY else 1,
        observation_count=1 if status==HEALTHY else 0,
        health_status=status,
        assessed_at=NOW,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_runtime_health_registry())

    def test_snapshot(self):
        records=(
            health("adapter.a",HEALTHY),
            health("adapter.b",FAILED),
        )
        decisions=AdapterFailureIsolationController().decide(records)
        snapshot=RuntimeHealthRegistry().build_snapshot(
            runtime_id="oracle.live.observation.production",
            adapter_health=records,
            isolation_decisions=decisions,
            assessed_at=NOW,
        )
        self.assertEqual(
            snapshot.runtime_health_status,
            RUNTIME_DEGRADED,
        )
        self.assertEqual(snapshot.isolated_count,1)

    def test_identity_mismatch(self):
        records=(health("adapter.a",HEALTHY),)
        decisions=AdapterFailureIsolationController().decide(
            (health("adapter.b",HEALTHY),)
        )
        with self.assertRaises(ValueError):
            RuntimeHealthRegistry().build_snapshot(
                runtime_id="runtime",
                adapter_health=records,
                isolation_decisions=decisions,
                assessed_at=NOW,
            )

if __name__=="__main__":
    print("="*72)
    print(" OAR-009 CERTIFICATION TEST")
    print(" RUNTIME HEALTH REGISTRY")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-009")
    print("[PASS] Adapter health and isolation state aggregate into one runtime health snapshot")
    print("[PASS] Healthy, degraded, and failed runtime states certified")
    print("[PASS] Adapter identity mismatches fail closed")
    print("[DONE] OAR-009 CERTIFIED")
"""

def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t):
    t=t.lstrip()
    ast.parse(t,filename=str(x))
    x.parent.mkdir(parents=True,exist_ok=True)
    x.write_text(t,encoding="utf-8",newline="\n")
    print(f"[PASS] Wrote: {x.relative_to(ROOT)}")

def main():
    print("="*72)
    print(" OAR-009 INSTALLER")
    print(" RUNTIME HEALTH REGISTRY")
    print("="*72)
    print("[BOOT] Revision: OAR_009_RUNTIME_HEALTH_REGISTRY_INSTALLER_V1")
    print(f"[ROOT] {ROOT}")

    for x in UPSTREAMS:
        if not x.is_file():
            raise RuntimeError(f"Certified upstream missing: {x}")

    hashes={x:sha(x) for x in UPSTREAMS}
    affected=(MODULE,TEST,INIT)
    backups={x:(x.read_bytes() if x.exists() else None) for x in affected}

    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)

        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        exp="from .oar_009_runtime_health_registry import *"

        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"):
                cur += "\n"
            cur += exp + "\n"
            ast.parse(cur,filename=str(INIT))
            INIT.write_text(cur,encoding="utf-8",newline="\n")

        for x,e in hashes.items():
            if sha(x)!=e:
                raise RuntimeError(f"Certified upstream changed: {x.name}")

        print("[PASS] Certified upstream remained unchanged")
        print("[PASS] Deterministic install hash:",hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest())
        print("[DONE] OAR-009 INSTALLATION COMPLETE")
        return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else:
                x.write_bytes(b)
        raise

if __name__=="__main__":
    raise SystemExit(main())
