from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oar_003_multi_adapter_runner.py",
    PACKAGE / "oar_007_adapter_health_model.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "oar_008_failure_isolation_controller.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_008_failure_isolation_controller.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass

from .oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    DEGRADED,
    FAILED,
)

BUILD_ID = "OAR-008"
OAR_008_REVISION = "OAR_008_FAILURE_ISOLATION_CONTROLLER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False

ACTION_CONTINUE = "continue"
ACTION_ISOLATE = "isolate"
ACTION_BLOCK = "block"


@dataclass(frozen=True, slots=True)
class AdapterIsolationDecision:
    adapter_id: str
    health_status: str
    action: str
    reason: str
    isolated: bool
    read_only: bool


class AdapterFailureIsolationController:
    read_only = True
    execution_allowed = False

    def decide(
        self,
        health_records: tuple[AdapterHealthRecord, ...],
    ) -> tuple[AdapterIsolationDecision, ...]:
        decisions = []

        seen = set()

        for record in sorted(
            health_records,
            key=lambda x: x.adapter_id,
        ):
            if record.adapter_id in seen:
                raise ValueError(
                    f"duplicate adapter health: {record.adapter_id}"
                )

            seen.add(record.adapter_id)

            if record.health_status == HEALTHY:
                action = ACTION_CONTINUE
                reason = "adapter_healthy"
                isolated = False
            elif record.health_status == DEGRADED:
                action = ACTION_ISOLATE
                reason = "adapter_degraded"
                isolated = True
            elif record.health_status == FAILED:
                action = ACTION_BLOCK
                reason = "adapter_failed"
                isolated = True
            else:
                raise ValueError(
                    f"unsupported health status: {record.health_status}"
                )

            decisions.append(
                AdapterIsolationDecision(
                    adapter_id=record.adapter_id,
                    health_status=record.health_status,
                    action=action,
                    reason=reason,
                    isolated=isolated,
                    read_only=True,
                )
            )

        return tuple(decisions)


def verify_failure_isolation_controller() -> bool:
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
    DEGRADED,
    FAILED,
)
from qseries_v2.observation_adapter_runtime.oar_008_failure_isolation_controller import (
    AdapterFailureIsolationController,
    ACTION_CONTINUE,
    ACTION_ISOLATE,
    ACTION_BLOCK,
    verify_failure_isolation_controller,
)

NOW = datetime(2026,8,12,4,50,tzinfo=timezone.utc)

def health(adapter_id, status):
    return AdapterHealthRecord(
        adapter_id=adapter_id,
        request_count=1,
        success_count=1 if status != FAILED else 0,
        failure_count=0 if status == HEALTHY else 1,
        observation_count=1 if status != FAILED else 0,
        health_status=status,
        assessed_at=NOW,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_failure_isolation_controller()
        )

    def test_actions(self):
        decisions = AdapterFailureIsolationController().decide(
            (
                health("adapter.a", HEALTHY),
                health("adapter.b", DEGRADED),
                health("adapter.c", FAILED),
            )
        )

        self.assertEqual(
            tuple(x.action for x in decisions),
            (
                ACTION_CONTINUE,
                ACTION_ISOLATE,
                ACTION_BLOCK,
            ),
        )

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            AdapterFailureIsolationController().decide(
                (
                    health("adapter.a", HEALTHY),
                    health("adapter.a", FAILED),
                )
            )

    def test_side_effects(self):
        controller = AdapterFailureIsolationController()
        self.assertTrue(controller.read_only)
        self.assertFalse(controller.execution_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-008 CERTIFICATION TEST")
    print(" ADAPTER FAILURE ISOLATION CONTROLLER")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-008")
    print("[PASS] Healthy, degraded, and failed adapters receive deterministic isolation decisions")
    print("[PASS] One failing adapter can be isolated without authorizing execution")
    print("[PASS] Duplicate adapter health fails closed")
    print("[DONE] OAR-008 CERTIFIED")
"""

def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x, t):
    t=t.lstrip()
    ast.parse(t,filename=str(x))
    x.parent.mkdir(parents=True,exist_ok=True)
    x.write_text(t,encoding="utf-8",newline="\n")
    print(f"[PASS] Wrote: {x.relative_to(ROOT)}")

def main():
    print("="*72)
    print(" OAR-008 INSTALLER")
    print(" ADAPTER FAILURE ISOLATION CONTROLLER")
    print("="*72)
    print("[BOOT] Revision: OAR_008_FAILURE_ISOLATION_CONTROLLER_INSTALLER_V1")
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
        exp="from .oar_008_failure_isolation_controller import *"

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
        print("[DONE] OAR-008 INSTALLATION COMPLETE")
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
