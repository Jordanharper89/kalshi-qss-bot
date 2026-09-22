from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION='OAD_168_CRYPTO_CONDITION_STATE_NORMALIZATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionState:\n    asset:str\n    source_family:str\n    metric_name:str\n    value:float\n    unit:str\n    condition:str\n    basis:str\n    independent_evidence:bool\n    market_native_reference:bool\n    observed_at:str|None\n\ndef _condition(metric):\n    n=metric.metric_name\n    v=float(metric.value)\n\n    # Transparent, non-predictive operational bands.\n    if n=="bid_ask_spread_bps":\n        if v<=5: return "TIGHT","spread_bps<=5"\n        if v<=20: return "NORMAL","5<spread_bps<=20"\n        return "WIDE","spread_bps>20"\n    if n=="fastest_fee_rate":\n        if v<10: return "LOW","sat_vb<10"\n        if v<50: return "ELEVATED","10<=sat_vb<50"\n        return "HIGH","sat_vb>=50"\n    if n=="fee_history_mean_gas_used_ratio" or n=="block_gas_utilization":\n        if v<0.40: return "LOW_UTILIZATION","ratio<0.40"\n        if v<0.80: return "ACTIVE","0.40<=ratio<0.80"\n        return "HIGH_UTILIZATION","ratio>=0.80"\n\n    # Metrics without defensible universal absolute bands remain observed,\n    # not force-classified.\n    return "OBSERVED","raw_metric_no_absolute_directional_band"\n\ndef normalize_crypto_condition_states(metrics):\n    out=[]\n    for m in tuple(metrics):\n        c,b=_condition(m)\n        out.append(CryptoConditionState(\n            m.asset,m.source_family,m.metric_name,m.value,m.unit,c,b,\n            m.independent_evidence,m.market_native_reference,m.observed_at\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_168_crypto_condition_state_normalization import normalize_crypto_condition_states\nclass T(unittest.TestCase):\n    def test_normalize(self):\n        metrics=(\n            SimpleNamespace(asset="BTC",source_family="coinbase",metric_name="bid_ask_spread_bps",value=2.0,unit="bps",independent_evidence=False,market_native_reference=True,observed_at=None),\n            SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",value=60.0,unit="sat/vB",independent_evidence=True,market_native_reference=False,observed_at=None),\n            SimpleNamespace(asset="BTC",source_family="coinbase",metric_name="spot_price",value=60000.0,unit="USD",independent_evidence=False,market_native_reference=True,observed_at=None),\n        )\n        r=normalize_crypto_condition_states(metrics)\n        print("[CONDITIONS]",tuple((x.metric_name,x.condition) for x in r))\n        self.assertEqual(r[0].condition,"TIGHT")\n        self.assertEqual(r[1].condition,"HIGH")\n        self.assertEqual(r[2].condition,"OBSERVED")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-168 crypto condition normalization certified")\n'

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
    module=pkg/'oad_168_crypto_condition_state_normalization.py'; test=r/'test_oad_168_crypto_condition_state_normalization.py'; init=pkg/"__init__.py"
    print("="*112)
    print(" OAD-168 CRYPTO CONDITION STATE NORMALIZATION INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_167_crypto_structured_condition_metric_extraction.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_168_crypto_condition_state_normalization import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-168 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
