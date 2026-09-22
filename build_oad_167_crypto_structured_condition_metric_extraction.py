from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION='OAD_167_CRYPTO_STRUCTURED_CONDITION_METRIC_EXTRACTION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom statistics import mean\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionMetric:\n    asset:str\n    source_family:str\n    metric_name:str\n    value:float\n    unit:str\n    observed_at:str|None\n    independent_evidence:bool\n    market_native_reference:bool\n\ndef _f(v):\n    try:\n        if v is None: return None\n        return float(v)\n    except Exception:\n        return None\n\ndef _emit(out,asset,family,name,value,unit,o,independent,market_native):\n    v=_f(value)\n    if v is not None:\n        out.append(CryptoConditionMetric(\n            asset,family,name,v,unit,getattr(o,"observed_at",None),\n            independent,market_native\n        ))\n\ndef extract_crypto_condition_metrics(cohort):\n    out=[]\n    for family,o in tuple(cohort.observations):\n        p=getattr(o,"payload",{}) or {}\n        typ=str(getattr(o,"observation_type",""))\n        if family=="coinbase":\n            asset=str(p.get("base_currency") or str(getattr(o,"subject","")).split("-")[0]).upper()\n            if asset not in ("BTC","ETH","SOL"): continue\n            _emit(out,asset,family,"spot_price",p.get("price"),"quote_currency",o,False,True)\n            _emit(out,asset,family,"spot_volume_24h",p.get("volume"),"base_currency",o,False,True)\n            bid=_f(p.get("bid")); ask=_f(p.get("ask"))\n            if bid is not None and ask is not None and bid>0 and ask>=bid:\n                mid=(bid+ask)/2.0\n                _emit(out,asset,family,"bid_ask_spread_bps",(ask-bid)/mid*10000.0,"bps",o,False,True)\n\n        elif family=="bitcoin":\n            if typ=="mempool_pressure":\n                _emit(out,"BTC",family,"mempool_transaction_count",p.get("count"),"transactions",o,True,False)\n                _emit(out,"BTC",family,"mempool_vsize",p.get("vsize"),"vbytes",o,True,False)\n                fees=p.get("recommended_fees") or {}\n                if isinstance(fees,dict):\n                    _emit(out,"BTC",family,"fastest_fee_rate",fees.get("fastestFee"),"sat/vB",o,True,False)\n                    _emit(out,"BTC",family,"half_hour_fee_rate",fees.get("halfHourFee"),"sat/vB",o,True,False)\n            elif typ=="tip_block_activity":\n                _emit(out,"BTC",family,"tip_block_tx_count",p.get("tx_count"),"transactions",o,True,False)\n                _emit(out,"BTC",family,"tip_block_weight",p.get("weight"),"weight_units",o,True,False)\n                _emit(out,"BTC",family,"tip_block_size",p.get("size"),"bytes",o,True,False)\n\n        elif family=="ethereum":\n            if typ=="execution_fee_pressure":\n                _emit(out,"ETH",family,"gas_price_wei",p.get("gas_price_wei"),"wei",o,True,False)\n                ratios=tuple(x for x in (p.get("gas_used_ratio") or ()) if _f(x) is not None)\n                if ratios:\n                    _emit(out,"ETH",family,"fee_history_mean_gas_used_ratio",mean(float(x) for x in ratios),"ratio",o,True,False)\n            elif typ in ("latest_block_transaction_pressure","finalized_block_activity"):\n                _emit(out,"ETH",family,"block_transaction_count",p.get("transaction_count"),"transactions",o,True,False)\n                gas_used=_f(p.get("gas_used")); gas_limit=_f(p.get("gas_limit"))\n                if gas_used is not None and gas_limit and gas_limit>0:\n                    _emit(out,"ETH",family,"block_gas_utilization",gas_used/gas_limit,"ratio",o,True,False)\n\n        elif family=="solana":\n            if typ=="mainnet_chain_state":\n                _emit(out,"SOL",family,"transaction_count",p.get("transaction_count"),"cumulative_transactions",o,True,False)\n                _emit(out,"SOL",family,"slot",p.get("slot"),"slot",o,True,False)\n                _emit(out,"SOL",family,"block_height",p.get("block_height"),"blocks",o,True,False)\n            elif typ=="finalized_block_activity":\n                _emit(out,"SOL",family,"finalized_block_signature_count",p.get("signature_count"),"signatures",o,True,False)\n                _emit(out,"SOL",family,"finalized_slot",p.get("slot"),"slot",o,True,False)\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_167_crypto_structured_condition_metric_extraction import extract_crypto_condition_metrics\n\nclass T(unittest.TestCase):\n    def test_extract(self):\n        obs=(\n            ("coinbase",SimpleNamespace(subject="BTC-USD",observation_type="live_ticker",observed_at="2026-08-29T00:00:00+00:00",payload={"base_currency":"BTC","price":"60000","volume":"123","bid":"59999","ask":"60001"})),\n            ("bitcoin",SimpleNamespace(subject="btc",observation_type="mempool_pressure",observed_at="2026-08-29T00:00:01+00:00",payload={"count":1000,"vsize":2000000,"recommended_fees":{"fastestFee":10,"halfHourFee":8}})),\n        )\n        r=extract_crypto_condition_metrics(SimpleNamespace(observations=obs))\n        names=tuple(x.metric_name for x in r)\n        print("[METRICS]",names)\n        self.assertIn("spot_price",names)\n        self.assertIn("bid_ask_spread_bps",names)\n        self.assertIn("mempool_transaction_count",names)\n        self.assertTrue(any(x.market_native_reference for x in r))\n        self.assertTrue(any(x.independent_evidence for x in r))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-167 structured crypto metric extraction certified")\n'

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
    module=pkg/'oad_167_crypto_structured_condition_metric_extraction.py'; test=r/'test_oad_167_crypto_structured_condition_metric_extraction.py'; init=pkg/"__init__.py"
    print("="*112)
    print(" OAD-167 CRYPTO STRUCTURED CONDITION METRIC EXTRACTION INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_166_crypto_cross_source_physical_runtime_certification.py', 'oad_163_crypto_live_multi_source_cohort.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_167_crypto_structured_condition_metric_extraction import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-167 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
