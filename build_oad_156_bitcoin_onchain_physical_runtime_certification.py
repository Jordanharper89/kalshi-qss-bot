from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_156_BITCOIN_ONCHAIN_PHYSICAL_RUNTIME_CERTIFICATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_156_bitcoin_onchain_physical_runtime_certification.py'; test=r/'test_oad_156_bitcoin_onchain_physical_runtime_certification.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-156 BITCOIN ON-CHAIN PHYSICAL RUNTIME CERTIFICATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_155_bitcoin_onchain_canonical_postgresql_persistence.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 156>=155:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified"); print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_155_bitcoin_onchain_canonical_postgresql_persistence import persist_current_bitcoin_onchain\nREAD_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass BitcoinPhysicalRuntimeCertification:\n    state:str; raw_observations:int; canonical_observations:int; committed_new:int\n    exact_readback:int; providers:tuple; source_class:str; independent_evidence:bool\n    runtime_ready:bool; certified_at:str; read_only:bool=True\n    probability_enabled:bool=False; execution_authority:bool=False\ndef run_bitcoin_onchain_physical_runtime_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    p=persist_current_bitcoin_onchain(root,timeout_seconds,acquisition_timeout_seconds)\n    required={"blockstream.info","mempool.space"}\n    ready=p.raw_observations>=4 and p.canonical_observations==p.raw_observations and p.exact_readback==p.canonical_observations and required.issubset(set(p.providers))\n    if not ready: raise RuntimeError("Bitcoin on-chain physical runtime certification failed")\n    return BitcoinPhysicalRuntimeCertification("READY",p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,p.providers,"underlying_chain_state_observation",True,True,datetime.now(timezone.utc).isoformat(),True,False,False)\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_156_bitcoin_onchain_physical_runtime_certification import run_bitcoin_onchain_physical_runtime_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_bitcoin_onchain_physical_runtime_certification()\n        print("[PHYSICAL] state=",r.state); print("[PHYSICAL] raw_observations=",r.raw_observations)\n        print("[PHYSICAL] canonical_observations=",r.canonical_observations); print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] providers=",r.providers)\n        print("[PHYSICAL] source_class=",r.source_class); print("[PHYSICAL] independent_evidence=",r.independent_evidence)\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready); self.assertEqual(set(r.providers),{"blockstream.info","mempool.space"})\n        self.assertTrue(r.independent_evidence); self.assertFalse(r.probability_enabled); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-156 Bitcoin on-chain physical runtime certified")\n    print("[PASS] public observer provenance preserved; Bitcoin Core local-node path remains future authority upgrade")\n    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_156_bitcoin_onchain_physical_runtime_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-156 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
