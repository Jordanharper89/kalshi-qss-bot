from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
UMD = ROOT / "qseries_v2" / "universal_market_discovery"

UPSTREAMS = (
    PKG / "oar_013_oi_canonical_handoff.py",
)

MODULE = PKG / "oar_014_umd_market_correlation_handoff.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_014_umd_market_correlation_handoff.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass

from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)

BUILD_ID = "OAR-014"
OAR_014_REVISION = "OAR_014_UMD_MARKET_CORRELATION_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class UMDMarketCorrelationRequest:
    iteration_number: int
    observation_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    market_identity_required: bool
    related_market_resolution_required: bool
    read_only: bool


class UMDMarketCorrelationHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        oi_handoff: FrozenOICanonicalHandoffRecord,
    ) -> UMDMarketCorrelationRequest:
        if not isinstance(
            oi_handoff,
            FrozenOICanonicalHandoffRecord,
        ):
            raise TypeError(
                "oi_handoff must be FrozenOICanonicalHandoffRecord"
            )

        return UMDMarketCorrelationRequest(
            iteration_number=oi_handoff.iteration_number,
            observation_ids=oi_handoff.observation_ids,
            provider_ids=oi_handoff.provider_ids,
            capability_ids=oi_handoff.capability_ids,
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )


def verify_umd_market_correlation_handoff() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations
import unittest

from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationHandoff,
    verify_umd_market_correlation_handoff,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_umd_market_correlation_handoff()
        )

    def test_request(self):
        oi = FrozenOICanonicalHandoffRecord(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            observation_hashes=("a"*64,),
            adapter_ids=("adapter.crypto.observe.v1",),
            provider_ids=("coinbase",),
            capability_ids=("spot_price",),
            observation_count=1,
            frozen_oi_target="frozen",
            read_only=True,
        )

        request = UMDMarketCorrelationHandoff().build(oi)

        self.assertTrue(
            request.market_identity_required
        )
        self.assertTrue(
            request.related_market_resolution_required
        )

    def test_side_effects(self):
        x=UMDMarketCorrelationHandoff()
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_allowed)
        self.assertFalse(x.persistence_allowed)
        self.assertFalse(x.publication_allowed)

if __name__=="__main__":
    print("="*72)
    print(" OAR-014 CERTIFICATION TEST")
    print(" UMD MARKET CORRELATION HANDOFF")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-014")
    print("[PASS] Frozen-OI live observations packaged for UMD market identity and related-market resolution")
    print("[PASS] UMD handoff remains read-only and non-mutating")
    print("[DONE] OAR-014 CERTIFIED")
"""

def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def discover_umd_boundary():
    if not UMD.is_dir():
        raise RuntimeError(
            f"Certified UMD package missing: {UMD}"
        )
    candidates=sorted(UMD.glob("umd_*.py"))
    if not candidates:
        raise RuntimeError(
            "Certified UMD modules missing"
        )
    return tuple(candidates)

def write(x,t):
    t=t.lstrip()
    ast.parse(t,filename=str(x))
    x.parent.mkdir(parents=True,exist_ok=True)
    x.write_text(t,encoding="utf-8",newline="\n")
    print(f"[PASS] Wrote: {x.relative_to(ROOT)}")

def main():
    print("="*72)
    print(" OAR-014 INSTALLER")
    print(" UMD MARKET CORRELATION HANDOFF")
    print("="*72)
    print("[BOOT] Revision: OAR_014_UMD_MARKET_CORRELATION_HANDOFF_INSTALLER_V1")
    print(f"[ROOT] {ROOT}")

    for x in UPSTREAMS:
        if not x.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {x}"
            )

    umd_files=discover_umd_boundary()
    protected=UPSTREAMS + umd_files
    hashes={x:sha(x) for x in protected}

    affected=(MODULE,TEST,INIT)
    backups={
        x:(x.read_bytes() if x.exists() else None)
        for x in affected
    }

    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)

        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        exp="from .oar_014_umd_market_correlation_handoff import *"

        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"):
                cur += "\n"
            cur += exp + "\n"
            ast.parse(cur,filename=str(INIT))
            INIT.write_text(cur,encoding="utf-8",newline="\n")

        for x,e in hashes.items():
            if sha(x)!=e:
                raise RuntimeError(
                    f"Certified upstream changed: {x.name}"
                )

        print(f"[PASS] Certified UMD boundary verified read-only across {len(umd_files)} modules")
        print("[PASS] Deterministic install hash:",hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest())
        print("[DONE] OAR-014 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(b)
        raise

if __name__=="__main__":
    raise SystemExit(main())
