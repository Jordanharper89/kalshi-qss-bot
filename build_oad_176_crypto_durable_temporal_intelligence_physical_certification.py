from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_176_CRYPTO_DURABLE_TEMPORAL_INTELLIGENCE_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoDurableTemporalPhysicalCertification:\n    seed_runtime_ready:bool\n    comparison_runtime_ready:bool\n    historical_states:int\n    exact_prior_states:int\n    comparable_temporal_metrics:int\n    increased:int\n    decreased:int\n    unchanged:int\n    no_comparable_history:int\n    cross_source_assets:tuple\n    exact_readback:int\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_durable_temporal_intelligence_physical_certification(\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n    lookback_seconds=21600.0,\n    history_limit=10000,\n):\n    seed_at=datetime.now(timezone.utc)\n    seed=run_crypto_durable_temporal_intelligence(\n        root=root,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        lookback_seconds=lookback_seconds,history_limit=history_limit,\n        snapshot_at=seed_at,\n    )\n    comparison_at=max(datetime.now(timezone.utc),seed_at+timedelta(microseconds=1))\n    comp=run_crypto_durable_temporal_intelligence(\n        root=root,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        lookback_seconds=lookback_seconds,history_limit=history_limit,\n        snapshot_at=comparison_at,\n    )\n    ready=bool(\n        seed.runtime_ready and comp.runtime_ready\n        and comp.historical_states>0\n        and comp.exact_prior_states>0\n        and comp.comparable_temporal_metrics>0\n        and comp.exact_readback==comp.current_states\n        and comp.cross_source_assets\n    )\n    if not ready:\n        raise RuntimeError(\n            "durable crypto temporal certification failed; "\n            f"seed_ready={seed.runtime_ready}; comp_ready={comp.runtime_ready}; "\n            f"history={comp.historical_states}; prior={comp.exact_prior_states}; "\n            f"comparable={comp.comparable_temporal_metrics}; readback={comp.exact_readback}"\n        )\n    return CryptoDurableTemporalPhysicalCertification(\n        seed.runtime_ready,comp.runtime_ready,comp.historical_states,\n        comp.exact_prior_states,comp.comparable_temporal_metrics,\n        comp.increased,comp.decreased,comp.unchanged,comp.no_comparable_history,\n        comp.cross_source_assets,comp.exact_readback,True,\n        datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_176_crypto_durable_temporal_intelligence_physical_certification import (\n    run_crypto_durable_temporal_intelligence_physical_certification,\n)\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_durable_temporal_intelligence_physical_certification()\n        print("[PHYSICAL] seed_runtime_ready=",r.seed_runtime_ready)\n        print("[PHYSICAL] comparison_runtime_ready=",r.comparison_runtime_ready)\n        print("[PHYSICAL] historical_states=",r.historical_states)\n        print("[PHYSICAL] exact_prior_states=",r.exact_prior_states)\n        print("[PHYSICAL] comparable_temporal_metrics=",r.comparable_temporal_metrics)\n        print("[PHYSICAL] increased=",r.increased)\n        print("[PHYSICAL] decreased=",r.decreased)\n        print("[PHYSICAL] unchanged=",r.unchanged)\n        print("[PHYSICAL] no_comparable_history=",r.no_comparable_history)\n        print("[PHYSICAL] cross_source_assets=",r.cross_source_assets)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertGreater(r.comparable_temporal_metrics,0)\n        self.assertGreater(r.exact_prior_states,0)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-176 durable crypto temporal intelligence physically certified")\n    print("[PASS] prior-state comparison is PostgreSQL-backed; prediction/direction/probability/execution remain disabled")\n'

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
    module=pkg/'oad_176_crypto_durable_temporal_intelligence_physical_certification.py'; test=r/'test_oad_176_crypto_durable_temporal_intelligence_physical_certification.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-176 CRYPTO DURABLE TEMPORAL INTELLIGENCE PHYSICAL CERTIFICATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_175_crypto_durable_temporal_intelligence_runtime.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_176_crypto_durable_temporal_intelligence_physical_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-176 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
