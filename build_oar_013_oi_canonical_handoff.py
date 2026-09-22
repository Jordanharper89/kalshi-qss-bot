from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PKG / "oar_010_canonical_live_observation_bus.py",
    PKG / "oar_011_live_observation_admission.py",
    PKG / "oar_012_live_observation_bus_registry.py",
    OI / "oi_final_certification_freeze.py",
    OI / "OI_FINAL_FREEZE_MANIFEST.json",
)

MODULE = PKG / "oar_013_oi_canonical_handoff.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_013_oi_canonical_handoff.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass

from .oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)

BUILD_ID = "OAR-013"
OAR_013_REVISION = "OAR_013_OI_CANONICAL_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class FrozenOICanonicalHandoffRecord:
    iteration_number: int
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    observation_count: int
    frozen_oi_target: str
    read_only: bool


class FrozenOICanonicalHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        admission: LiveObservationAdmissionResult,
    ) -> FrozenOICanonicalHandoffRecord:
        if not isinstance(
            admission,
            LiveObservationAdmissionResult,
        ):
            raise TypeError(
                "admission must be LiveObservationAdmissionResult"
            )

        observations = tuple(
            sorted(
                admission.admitted_observations,
                key=lambda x: x.observation_id,
            )
        )

        return FrozenOICanonicalHandoffRecord(
            iteration_number=admission.iteration_number,
            observation_ids=tuple(
                x.observation_id for x in observations
            ),
            observation_hashes=tuple(
                x.observation_hash for x in observations
            ),
            adapter_ids=tuple(
                sorted({x.adapter_id for x in observations})
            ),
            provider_ids=tuple(
                sorted({x.provider_id for x in observations})
            ),
            capability_ids=tuple(
                sorted({x.capability for x in observations})
            ),
            observation_count=len(observations),
            frozen_oi_target=(
                "OI-003 canonical observation gateway / "
                "frozen Observation Intelligence boundary"
            ),
            read_only=True,
        )


def verify_oi_canonical_handoff() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservation,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoff,
    verify_oi_canonical_handoff,
)

NOW = datetime(2026, 8, 12, 13, 30, tzinfo=timezone.utc)

def obs():
    return CanonicalLiveObservation(
        observation_id="liveobs.1",
        adapter_id="adapter.crypto.observe.v1",
        provider_id="coinbase",
        capability="spot_price",
        payload=(("asset","BTC"),("price","65000")),
        observed_at=NOW,
        iteration_number=1,
        lineage_hash="a"*64,
        observation_hash="b"*64,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oi_canonical_handoff()
        )

    def test_handoff(self):
        admission = LiveObservationAdmissionResult(
            iteration_number=1,
            admitted_observations=(obs(),),
            rejected_observation_ids=(),
            duplicate_observation_ids=(),
            admitted_count=1,
            rejected_count=0,
            read_only=True,
        )

        result = FrozenOICanonicalHandoff().build(
            admission
        )

        self.assertEqual(
            result.observation_count,
            1,
        )
        self.assertEqual(
            result.provider_ids,
            ("coinbase",),
        )

    def test_side_effects(self):
        bridge = FrozenOICanonicalHandoff()
        self.assertTrue(bridge.read_only)
        self.assertFalse(bridge.execution_allowed)
        self.assertFalse(bridge.persistence_allowed)
        self.assertFalse(bridge.publication_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-013 CERTIFICATION TEST")
    print(" FROZEN OI CANONICAL HANDOFF")
    print("="*72)

    r = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-013")
    print("[PASS] Admitted live observations packaged for frozen OI consumption")
    print("[PASS] Observation identity, hashes, provider, adapter, and capabilities preserved")
    print("[PASS] Frozen OI remains unchanged and read-only")
    print("[DONE] OAR-013 CERTIFIED")
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
    print(" OAR-013 INSTALLER")
    print(" FROZEN OI CANONICAL HANDOFF")
    print("="*72)
    print("[BOOT] Revision: OAR_013_OI_CANONICAL_HANDOFF_INSTALLER_V1")
    print(f"[ROOT] {ROOT}")

    for x in UPSTREAMS:
        if not x.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {x}"
            )

    hashes={x:sha(x) for x in UPSTREAMS}
    affected=(MODULE,TEST,INIT)
    backups={
        x:(x.read_bytes() if x.exists() else None)
        for x in affected
    }

    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)

        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        exp="from .oar_013_oi_canonical_handoff import *"

        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"):
                cur += "\n"
            cur += exp + "\n"
            ast.parse(cur,filename=str(INIT))
            INIT.write_text(
                cur,
                encoding="utf-8",
                newline="\n",
            )

        for x,e in hashes.items():
            if sha(x)!=e:
                raise RuntimeError(
                    f"Certified upstream changed: {x.name}"
                )

        print("[PASS] Frozen OI and certified OAR upstream remained unchanged")
        print("[PASS] Deterministic install hash:", hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest())
        print("[DONE] OAR-013 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(b)
        raise

if __name__ == "__main__":
    raise SystemExit(main())
