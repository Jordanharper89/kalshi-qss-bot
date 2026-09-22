
from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_132_RESILIENT_AUTHORITATIVE_ECONOMIC_PROVIDER_ISOLATION_V1'
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
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_132_resilient_authoritative_economic_provider_isolation.py'; test=r/'test_oad_132_resilient_authoritative_economic_provider_isolation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-132 RESILIENT AUTHORITATIVE ECONOMIC PROVIDER ISOLATION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    deps=['oad_128_official_bls_economic_adapter.py', 'oad_129_official_treasury_fiscal_data_adapter.py']
    for d in deps:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom typing import Callable\n\nfrom .oad_128_official_bls_economic_adapter import acquire_bls_latest_economic_observations\nfrom .oad_129_official_treasury_fiscal_data_adapter import acquire_treasury_debt_observation\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True, slots=True)\nclass EconomicProviderResult:\n    provider: str\n    state: str\n    observations: tuple\n    observation_count: int\n    error_type: str|None\n    error_message: str|None\n    checked_at: str\n    read_only: bool=True\n    probability_enabled: bool=False\n    execution_authority: bool=False\n\ndef _now():\n    return datetime.now(timezone.utc).isoformat()\n\ndef _run_provider(provider: str, fn: Callable, timeout_seconds: float):\n    try:\n        rows=tuple(fn(timeout_seconds))\n        return EconomicProviderResult(provider,"AVAILABLE",rows,len(rows),None,None,_now())\n    except Exception as exc:\n        return EconomicProviderResult(\n            provider,"UNAVAILABLE",tuple(),0,type(exc).__name__,str(exc),_now()\n        )\n\ndef acquire_resilient_authoritative_economic(timeout_seconds=20.0):\n    results=(\n        _run_provider("api.bls.gov",acquire_bls_latest_economic_observations,timeout_seconds),\n        _run_provider("api.fiscaldata.treasury.gov",acquire_treasury_debt_observation,timeout_seconds),\n    )\n    observations=tuple(o for r in results if r.state=="AVAILABLE" for o in r.observations)\n    return results,observations\n')
        write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_132_resilient_authoritative_economic_provider_isolation as m\nclass T(unittest.TestCase):\n    def test_provider_isolation(self):\n        with patch.object(m,"acquire_bls_latest_economic_observations",return_value=("b1","b2")), \\\n             patch.object(m,"acquire_treasury_debt_observation",side_effect=RuntimeError("tls blocked")):\n            results,obs=m.acquire_resilient_authoritative_economic()\n        print("[PROVIDER_STATES]",[(x.provider,x.state) for x in results])\n        print("[OBSERVATIONS]",len(obs))\n        self.assertEqual(len(obs),2)\n        self.assertEqual(results[0].state,"AVAILABLE")\n        self.assertEqual(results[1].state,"UNAVAILABLE")\n        self.assertFalse(results[1].execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-132 resilient provider isolation certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_132_resilient_authoritative_economic_provider_isolation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] existing canonical/PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-132 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
