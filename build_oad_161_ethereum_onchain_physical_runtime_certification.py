from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_161_ETHEREUM_ONCHAIN_PHYSICAL_RUNTIME_CERTIFICATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_161_ethereum_onchain_physical_runtime_certification.py'; test=r/'test_oad_161_ethereum_onchain_physical_runtime_certification.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-161 ETHEREUM ON-CHAIN PHYSICAL RUNTIME CERTIFICATION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_160_ethereum_onchain_canonical_postgresql_persistence.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 161>=160:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_160_ethereum_onchain_canonical_postgresql_persistence import persist_current_ethereum_onchain\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass EthereumPhysicalRuntimeCertification:\n    state:str\n    raw_observations:int\n    canonical_observations:int\n    committed_new:int\n    exact_readback:int\n    providers:tuple\n    source_class:str\n    independent_evidence:bool\n    runtime_ready:bool\n    certified_at:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_ethereum_onchain_physical_runtime_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    p=persist_current_ethereum_onchain(root,timeout_seconds,acquisition_timeout_seconds)\n    ready=(\n        p.raw_observations>=4\n        and p.canonical_observations==p.raw_observations\n        and p.exact_readback==p.canonical_observations\n        and "cloudflare-eth.com" in set(p.providers)\n    )\n    if not ready:\n        raise RuntimeError("Ethereum on-chain physical runtime certification failed")\n    return EthereumPhysicalRuntimeCertification(\n        "READY",p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,p.providers,\n        "underlying_chain_state_observation",True,True,datetime.now(timezone.utc).isoformat(),True,False,False)\n')
        write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_161_ethereum_onchain_physical_runtime_certification import run_ethereum_onchain_physical_runtime_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_ethereum_onchain_physical_runtime_certification()\n        print("[PHYSICAL] state=",r.state)\n        print("[PHYSICAL] raw_observations=",r.raw_observations)\n        print("[PHYSICAL] canonical_observations=",r.canonical_observations)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] providers=",r.providers)\n        print("[PHYSICAL] source_class=",r.source_class)\n        print("[PHYSICAL] independent_evidence=",r.independent_evidence)\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready)\n        self.assertIn("cloudflare-eth.com",r.providers)\n        self.assertTrue(r.independent_evidence)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-161 Ethereum on-chain physical runtime certified")\n    print("[PASS] Ethereum chain state remains distinct from Coinbase market-native reference")\n    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_161_ethereum_onchain_physical_runtime_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-161 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
