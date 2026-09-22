from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_146_COINBASE_CRYPTO_PHYSICAL_RUNTIME_READINESS_GATE_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_146_coinbase_crypto_physical_runtime_readiness_gate.py'; test=r/'test_oad_146_coinbase_crypto_physical_runtime_readiness_gate.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-146 COINBASE CRYPTO PHYSICAL RUNTIME READINESS GATE INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_143_coinbase_public_product_universe_discovery.py', 'oad_145_coinbase_market_native_canonical_persistence.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
    if 146==145 and not oph.is_file(): raise RuntimeError("Required OPH-019 universal queue missing")
    if 146==145: print("[PASS] dependency verified: OPH-019 universal PostgreSQL ingestion queue")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_143_coinbase_public_product_universe_discovery import discover_coinbase_public_products\nfrom .oad_145_coinbase_market_native_canonical_persistence import persist_current_coinbase_market_native\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CoinbasePhysicalRuntimeGate:\n    state:str\n    discovered_products:int\n    acquired_observations:int\n    canonical_observations:int\n    committed_new:int\n    exact_readback:int\n    market_native_reference:bool\n    independent_evidence:bool\n    runtime_ready:bool\n    certified_at:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_coinbase_crypto_physical_runtime_readiness_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,max_products=25):\n    products=discover_coinbase_public_products(acquisition_timeout_seconds,limit=max_products)\n    if not products: raise RuntimeError("Coinbase public product discovery returned zero usable products")\n    p=persist_current_coinbase_market_native(root,timeout_seconds,acquisition_timeout_seconds,max_products)\n    ready=p.raw_observations>0 and p.canonical_observations==p.raw_observations and p.exact_readback==p.canonical_observations\n    if not ready: raise RuntimeError("Coinbase physical runtime readiness failed")\n    return CoinbasePhysicalRuntimeGate("READY",len(products),p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,True,False,True,datetime.now(timezone.utc).isoformat(),True,False,False)\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_146_coinbase_crypto_physical_runtime_readiness_gate import run_coinbase_crypto_physical_runtime_readiness_gate\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_coinbase_crypto_physical_runtime_readiness_gate()\n        print("[PHYSICAL] state=",r.state)\n        print("[PHYSICAL] discovered_products=",r.discovered_products)\n        print("[PHYSICAL] acquired_observations=",r.acquired_observations)\n        print("[PHYSICAL] canonical_observations=",r.canonical_observations)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] market_native_reference=",r.market_native_reference)\n        print("[PHYSICAL] independent_evidence=",r.independent_evidence)\n        print("[PHYSICAL] runtime_ready=",r.runtime_ready)\n        self.assertTrue(r.runtime_ready); self.assertTrue(r.market_native_reference)\n        self.assertFalse(r.independent_evidence); self.assertFalse(r.probability_enabled); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-146 Coinbase crypto physical runtime readiness certified")\n    print("[PASS] Coinbase remains market-native reference, not independent evidence")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_146_coinbase_crypto_physical_runtime_readiness_gate import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-146 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
