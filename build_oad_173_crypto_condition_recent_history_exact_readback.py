from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_173_CRYPTO_CONDITION_RECENT_HISTORY_EXACT_READBACK_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (\n    CanonicalPersistenceQueryRequest,\n)\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_168_crypto_condition_state_normalization import CryptoConditionState\nfrom .oad_172_crypto_condition_snapshot_postgresql_persistence import SOURCE_PREFIX\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nDEFAULT_LOOKBACK_SECONDS=21600.0\nDEFAULT_LIMIT=10000\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionHistoryReadback:\n    observed_from:str\n    observed_to:str\n    queried_rows:int\n    condition_rows:int\n    states:tuple\n    read_only:bool=True\n\ndef _state_from_row(row):\n    if not str(row.source_id).startswith(SOURCE_PREFIX):\n        return None\n    p=dict(row.payload)\n    if row.observation_type!="crypto_condition_snapshot":\n        return None\n    return CryptoConditionState(\n        asset=str(p["asset"]),\n        source_family=str(p["source_family"]),\n        metric_name=str(p["metric_name"]),\n        value=float(p["value"]),\n        unit=str(p["unit"]),\n        condition=str(p["condition"]),\n        basis=str(p["basis"]),\n        independent_evidence=bool(p["independent_evidence"]),\n        market_native_reference=bool(p["market_native_reference"]),\n        observed_at=row.observed_at.isoformat(),\n    )\n\ndef read_recent_crypto_condition_history(root=None,lookback_seconds=DEFAULT_LOOKBACK_SECONDS,limit=DEFAULT_LIMIT,now=None):\n    root=Path(root or Path.cwd()).resolve()\n    end=now or datetime.now(timezone.utc)\n    if end.tzinfo is None: end=end.replace(tzinfo=timezone.utc)\n    end=end.astimezone(timezone.utc)\n    start=end-timedelta(seconds=float(lookback_seconds))\n    backend=_backend(root)\n    request=CanonicalPersistenceQueryRequest.by_observed_time_range(\n        query_id=f"query.oad173.crypto-condition-history.{int(end.timestamp())}",\n        backend_id=backend.backend_id,\n        observed_from=start,\n        observed_to=end,\n        limit=int(limit),\n        requested_at=datetime.now(timezone.utc),\n        query_metadata={\n            "read_only":True,\n            "build_id":"OAD-173",\n            "query_mode":"bounded_recent_time_range_then_condition_prefix_filter",\n            "lookback_seconds":float(lookback_seconds),\n        },\n    )\n    rows=tuple(backend.query(request=request))\n    states=tuple(x for x in (_state_from_row(r) for r in rows) if x is not None)\n    states=tuple(sorted(states,key=lambda x:(str(x.observed_at),x.asset,x.source_family,x.metric_name)))\n    return CryptoConditionHistoryReadback(\n        start.isoformat(),end.isoformat(),len(rows),len(states),states,True\n    )\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_173_crypto_condition_recent_history_exact_readback as m\nclass Fake:\n    backend_id="fake"\n    def query(self,request):\n        self.request=request\n        return (\n            SimpleNamespace(\n                source_id="source.crypto.condition.eth.ethereum.gas_price_wei",\n                observation_type="crypto_condition_snapshot",\n                observed_at=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc),\n                payload=tuple({\n                    "asset":"ETH","source_family":"ethereum","metric_name":"gas_price_wei",\n                    "value":100.0,"unit":"wei","condition":"OBSERVED","basis":"raw",\n                    "independent_evidence":True,"market_native_reference":False,\n                }.items())\n            ),\n            SimpleNamespace(source_id="source.other",observation_type="x",observed_at=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc),payload=()),\n        )\nclass T(unittest.TestCase):\n    def test_bounded_read(self):\n        b=Fake()\n        with patch.object(m,"_backend",return_value=b):\n            r=m.read_recent_crypto_condition_history(now=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc),lookback_seconds=3600,limit=100)\n        print("[QUERY_TYPE]",b.request.query_type)\n        print("[QUERIED]",r.queried_rows,"[CONDITIONS]",r.condition_rows)\n        self.assertEqual(b.request.query_type,"by_observed_time_range")\n        self.assertEqual(b.request.limit,100)\n        self.assertEqual(r.condition_rows,1)\n        self.assertEqual(r.states[0].asset,"ETH")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-173 bounded recent PostgreSQL condition-history readback certified")\n'

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
    module=pkg/'oad_173_crypto_condition_recent_history_exact_readback.py'; test=r/'test_oad_173_crypto_condition_recent_history_exact_readback.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-173 CRYPTO CONDITION RECENT HISTORY EXACT READBACK INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_172_crypto_condition_snapshot_postgresql_persistence.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_173_crypto_condition_recent_history_exact_readback import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-173 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
