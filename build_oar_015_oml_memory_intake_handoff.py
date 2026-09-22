from __future__ import annotations
import ast, hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"

OML_CANDIDATES = (
    ROOT / "qseries_v2" / "oracle_memory",
    ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_memory",
)

UPSTREAMS = (
    PKG / "oar_013_oi_canonical_handoff.py",
    PKG / "oar_014_umd_market_correlation_handoff.py",
)

MODULE = PKG / "oar_015_oml_memory_intake_handoff.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_015_oml_memory_intake_handoff.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass

from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from .oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)

BUILD_ID = "OAR-015"
OAR_015_REVISION = "OAR_015_OML_MEMORY_INTAKE_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OMLMemoryIntakeRequest:
    iteration_number: int
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    provider_ids: tuple[str, ...]
    requires_market_identity_resolution: bool
    requires_evidence_lineage_preservation: bool
    requires_contradiction_preservation: bool
    read_only: bool


class OMLMemoryIntakeHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        *,
        oi_handoff: FrozenOICanonicalHandoffRecord,
        umd_request: UMDMarketCorrelationRequest,
    ) -> OMLMemoryIntakeRequest:
        if not isinstance(
            oi_handoff,
            FrozenOICanonicalHandoffRecord,
        ):
            raise TypeError(
                "oi_handoff must be FrozenOICanonicalHandoffRecord"
            )

        if not isinstance(
            umd_request,
            UMDMarketCorrelationRequest,
        ):
            raise TypeError(
                "umd_request must be UMDMarketCorrelationRequest"
            )

        if (
            oi_handoff.iteration_number
            != umd_request.iteration_number
        ):
            raise ValueError(
                "OI/UMD iteration lineage mismatch"
            )

        if (
            oi_handoff.observation_ids
            != umd_request.observation_ids
        ):
            raise ValueError(
                "OI/UMD observation identity mismatch"
            )

        return OMLMemoryIntakeRequest(
            iteration_number=oi_handoff.iteration_number,
            observation_ids=oi_handoff.observation_ids,
            observation_hashes=oi_handoff.observation_hashes,
            provider_ids=oi_handoff.provider_ids,
            requires_market_identity_resolution=True,
            requires_evidence_lineage_preservation=True,
            requires_contradiction_preservation=True,
            read_only=True,
        )


def verify_oml_memory_intake_handoff() -> bool:
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
)
from qseries_v2.observation_adapter_runtime.oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeHandoff,
    verify_oml_memory_intake_handoff,
)

def oi():
    return FrozenOICanonicalHandoffRecord(
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

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oml_memory_intake_handoff()
        )

    def test_request(self):
        a=oi()
        u=UMDMarketCorrelationHandoff().build(a)
        r=OMLMemoryIntakeHandoff().build(
            oi_handoff=a,
            umd_request=u,
        )
        self.assertTrue(
            r.requires_market_identity_resolution
        )
        self.assertTrue(
            r.requires_evidence_lineage_preservation
        )

    def test_lineage_mismatch(self):
        a=oi()
        u=UMDMarketCorrelationHandoff().build(a)
        bad=type(u)(
            iteration_number=2,
            observation_ids=u.observation_ids,
            provider_ids=u.provider_ids,
            capability_ids=u.capability_ids,
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )
        with self.assertRaises(ValueError):
            OMLMemoryIntakeHandoff().build(
                oi_handoff=a,
                umd_request=bad,
            )

if __name__=="__main__":
    print("="*72)
    print(" OAR-015 CERTIFICATION TEST")
    print(" OML MEMORY INTAKE HANDOFF")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-015")
    print("[PASS] Live observation identity and lineage packaged for frozen Oracle Memory intake")
    print("[PASS] UMD market-resolution dependency remains explicit")
    print("[PASS] OML boundary remains read-only; persistence is not enabled by OAR")
    print("[DONE] OAR-015 CERTIFIED")
"""

def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def discover_oml_boundary():
    existing=[
        x for x in OML_CANDIDATES
        if x.is_dir()
    ]
    if not existing:
        raise RuntimeError(
            "Certified Oracle Memory package missing"
        )

    files=[]
    for root in existing:
        files.extend(root.glob("*.py"))
        files.extend(root.glob("**/oml_*.py"))

    unique=tuple(sorted(set(files)))

    if not unique:
        raise RuntimeError(
            "Certified Oracle Memory modules missing"
        )

    return unique

def write(x,t):
    t=t.lstrip()
    ast.parse(t,filename=str(x))
    x.parent.mkdir(parents=True,exist_ok=True)
    x.write_text(t,encoding="utf-8",newline="\n")
    print(f"[PASS] Wrote: {x.relative_to(ROOT)}")

def main():
    print("="*72)
    print(" OAR-015 INSTALLER")
    print(" OML MEMORY INTAKE HANDOFF")
    print("="*72)
    print("[BOOT] Revision: OAR_015_OML_MEMORY_INTAKE_HANDOFF_INSTALLER_V1")
    print(f"[ROOT] {ROOT}")

    for x in UPSTREAMS:
        if not x.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {x}"
            )

    oml_files=discover_oml_boundary()
    protected=UPSTREAMS + oml_files
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
        exp="from .oar_015_oml_memory_intake_handoff import *"

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

        print(f"[PASS] Certified Oracle Memory boundary verified read-only across {len(oml_files)} modules")
        print("[PASS] Deterministic install hash:",hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest())
        print("[DONE] OAR-015 INSTALLATION COMPLETE")
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