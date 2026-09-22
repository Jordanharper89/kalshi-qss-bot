from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"observation_adapter_runtime"
OI=ROOT/"qseries_v2"/"observation_intelligence"
UP=(PKG/"oar_013_oi_canonical_handoff.py",PKG/"oar_014_umd_market_correlation_handoff.py",PKG/"oar_015_oml_memory_intake_handoff.py",PKG/"oar_016_umd_boundary_resolver.py",PKG/"oar_017_oml_boundary_resolver.py",OI/"oi_final_certification_freeze.py")
MOD=PKG/"oar_018_oi_umd_oml_integration.py"
INIT=PKG/"__init__.py"
TEST=ROOT/"test_oar_018_oi_umd_oml_integration.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from .oar_013_oi_canonical_handoff import FrozenOICanonicalHandoffRecord
from .oar_014_umd_market_correlation_handoff import UMDMarketCorrelationHandoff,UMDMarketCorrelationRequest
from .oar_015_oml_memory_intake_handoff import OMLMemoryIntakeHandoff,OMLMemoryIntakeRequest
BUILD_ID="OAR-018"
OAR_018_REVISION="OAR_018_OI_UMD_OML_INTEGRATION_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PERSISTENCE_ALLOWED=False
PUBLICATION_ALLOWED=False
@dataclass(frozen=True,slots=True)
class OIUMDOMLIntegrationPackage:
    oi_handoff:FrozenOICanonicalHandoffRecord
    umd_request:UMDMarketCorrelationRequest
    oml_request:OMLMemoryIntakeRequest
    observation_count:int
    lineage_valid:bool
    read_only:bool
class OIUMDOMLIntegrationBuilder:
    read_only=True
    execution_allowed=False
    persistence_allowed=False
    publication_allowed=False
    def build(self,oi_handoff:FrozenOICanonicalHandoffRecord)->OIUMDOMLIntegrationPackage:
        if not isinstance(oi_handoff,FrozenOICanonicalHandoffRecord): raise TypeError("oi_handoff must be FrozenOICanonicalHandoffRecord")
        u=UMDMarketCorrelationHandoff().build(oi_handoff)
        o=OMLMemoryIntakeHandoff().build(oi_handoff=oi_handoff,umd_request=u)
        valid=(oi_handoff.iteration_number==u.iteration_number==o.iteration_number and oi_handoff.observation_ids==u.observation_ids==o.observation_ids)
        if not valid: raise ValueError("OI -> UMD -> OML lineage invalid")
        return OIUMDOMLIntegrationPackage(oi_handoff,u,o,oi_handoff.observation_count,True,True)
def verify_oi_umd_oml_integration()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PERSISTENCE_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
"""
TESTSRC=r"""
from __future__ import annotations
import unittest
from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import FrozenOICanonicalHandoffRecord
from qseries_v2.observation_adapter_runtime.oar_018_oi_umd_oml_integration import *
def h():
    return FrozenOICanonicalHandoffRecord(1,("liveobs.1",),("a"*64,),("adapter.crypto.observe.v1",),("coinbase",),("spot_price",),1,"frozen",True)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_oi_umd_oml_integration())
    def test_build(self):
        r=OIUMDOMLIntegrationBuilder().build(h()); self.assertTrue(r.lineage_valid); self.assertEqual(r.observation_count,1)
if __name__=="__main__":
    print("="*72); print(" OAR-018 CERTIFICATION TEST"); print(" OI -> UMD -> OML INTEGRATION PACKAGE"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-018"); print("[PASS] Frozen OI, UMD, and OML handoffs form one lineage-valid integration package"); print("[PASS] Integration remains read-only with persistence and execution disabled"); print("[DONE] OAR-018 CERTIFIED")
"""
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t):
    t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding="utf-8",newline="\n"); print("[PASS] Wrote:",x.relative_to(ROOT))
def main():
    print("="*72); print(" OAR-018 INSTALLER"); print(" OI -> UMD -> OML INTEGRATION PACKAGE"); print("="*72); print("[BOOT] Revision: OAR_018_OI_UMD_OML_INTEGRATION_INSTALLER_V1"); print("[ROOT]",ROOT)
    for x in UP:
        if not x.is_file(): raise RuntimeError(f"Certified upstream missing: {x}")
    h={x:sha(x) for x in UP}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; exp="from .oar_018_oi_umd_oml_integration import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"): cur+="\n"
            cur+=exp+"\n"; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding="utf-8",newline="\n")
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f"Certified upstream changed: {x.name}")
        print("[PASS] Certified OAR and frozen OI upstream remained unchanged"); print("[PASS] Deterministic install hash:",hashlib.sha256(MOD.read_bytes()+TEST.read_bytes()).hexdigest()); print("[DONE] OAR-018 INSTALLATION COMPLETE"); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=="__main__": raise SystemExit(main())
