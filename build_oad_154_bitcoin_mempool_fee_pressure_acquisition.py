from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_154_BITCOIN_MEMPOOL_FEE_PRESSURE_ACQUISITION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_154_bitcoin_mempool_fee_pressure_acquisition.py'; test=r/'test_oad_154_bitcoin_mempool_fee_pressure_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-154 BITCOIN MEMPOOL AND FEE PRESSURE ACQUISITION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_152_bitcoin_onchain_evidence_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 154>=155:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified"); print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\nfrom .oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation,utcnow_iso\nBASE="https://mempool.space/api"; PROVIDER="mempool.space"\nREAD_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False\ndef _get_json(url,timeout_seconds):\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r: return json.loads(r.read().decode("utf-8"))\ndef acquire_bitcoin_mempool_pressure_observations(timeout_seconds=20.0):\n    mempool=_get_json(BASE+"/mempool",timeout_seconds)\n    fees=_get_json(BASE+"/v1/fees/recommended",timeout_seconds)\n    recent=_get_json(BASE+"/mempool/recent",timeout_seconds); now=utcnow_iso()\n    pressure=build_bitcoin_onchain_observation(source_id=f"bitcoin:mempool:pressure:{mempool.get(\'count\')}:{mempool.get(\'vsize\')}:{now}",provider=PROVIDER,provider_role="public_mempool_observer",observation_type="mempool_pressure",subject="Bitcoin mainnet mempool pressure",observed_at=now,source_url=BASE+"/mempool",payload={"count":mempool.get("count"),"vsize":mempool.get("vsize"),"total_fee":mempool.get("total_fee"),"fee_histogram":mempool.get("fee_histogram"),"recommended_fees":fees})\n    activity=build_bitcoin_onchain_observation(source_id=f"bitcoin:mempool:recent:{len(recent) if isinstance(recent,list) else 0}:{now}",provider=PROVIDER,provider_role="public_mempool_observer",observation_type="recent_unconfirmed_activity",subject="Bitcoin recent unconfirmed activity",observed_at=now,source_url=BASE+"/mempool/recent",payload={"recent_transactions":tuple(recent[:10]) if isinstance(recent,list) else tuple()})\n    if not validate_bitcoin_onchain_observation(pressure) or not validate_bitcoin_onchain_observation(activity): raise RuntimeError("Bitcoin mempool observation validation failed")\n    return (pressure,activity)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_154_bitcoin_mempool_fee_pressure_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        def get(url,timeout):\n            if url.endswith("/mempool"): return {"count":1000,"vsize":2000000,"total_fee":123,"fee_histogram":[[1,2]]}\n            if url.endswith("/recommended"): return {"fastestFee":10,"halfHourFee":8,"hourFee":5,"economyFee":2,"minimumFee":1}\n            if url.endswith("/recent"): return [{"txid":"a","fee":1000,"vsize":200,"value":50000}]\n            raise AssertionError(url)\n        with patch.object(m,"_get_json",side_effect=get):\n            r=m.acquire_bitcoin_mempool_pressure_observations()\n        print("[OBSERVATIONS]",len(r)); print("[MEMPOOL_COUNT]",r[0].payload["count"]); print("[RECENT]",len(r[1].payload["recent_transactions"]))\n        self.assertEqual(len(r),2); self.assertEqual(r[0].payload["count"],1000)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-154 Bitcoin mempool/fee-pressure acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_154_bitcoin_mempool_fee_pressure_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-154 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
