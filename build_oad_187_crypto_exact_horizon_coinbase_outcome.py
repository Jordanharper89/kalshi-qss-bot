from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_187_CRYPTO_EXACT_HORIZON_COINBASE_OUTCOME_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom hashlib import sha256\nimport json,urllib.parse,urllib.request\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation,verify_outcome_observation\n\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False\nPRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}\nCOINBASE_CANDLES="https://api.exchange.coinbase.com/products/{product}/candles"\n\ndef _dt(v):\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass ExactHorizonCryptoOutcome:\n    experience_id:str; asset:str; horizon_seconds:int; matures_at:str; candle_start:str\n    start_price:float; outcome_price:float; return_fraction:float; return_percent:float\n    source_ref:str; source_hash:str; outcome_observation:object\n    exact_interval:bool=True; read_only:bool=True; execution_authority:bool=False\n\ndef experience_start_spot_price(experience):\n    rows=[x for x in tuple(experience.condition_vector) if str(x[0])=="coinbase" and str(x[1])=="spot_price"]\n    if len(rows)!=1: raise RuntimeError("experience must contain exactly one Coinbase spot_price")\n    v=float(rows[0][2])\n    if v<=0: raise RuntimeError("invalid experience start price")\n    return v\n\ndef select_first_candle_at_or_after(rows,matures_at):\n    target=int(_dt(matures_at).timestamp())\n    valid=sorted((tuple(x) for x in rows if len(tuple(x))>=5 and int(tuple(x)[0])>=target),key=lambda x:int(x[0]))\n    if not valid: raise RuntimeError("no Coinbase one-minute candle at/after maturity")\n    return valid[0]\n\ndef acquire_exact_coinbase_outcome(experience,horizon_seconds=60,timeout_seconds=20.0,opener=None):\n    start=_dt(experience.snapshot_at).astimezone(timezone.utc)\n    maturity=start+timedelta(seconds=int(horizon_seconds))\n    product=PRODUCTS[experience.asset]\n    q=urllib.parse.urlencode({\n        "granularity":60,\n        "start":(maturity-timedelta(seconds=60)).isoformat().replace("+00:00","Z"),\n        "end":(maturity+timedelta(seconds=180)).isoformat().replace("+00:00","Z"),\n    })\n    url=COINBASE_CANDLES.format(product=product)+"?"+q\n    req=urllib.request.Request(url,headers={"User-Agent":"Q-Series-Oracle/1.0","Accept":"application/json"})\n    raw=(opener or urllib.request.urlopen)(req,timeout=float(timeout_seconds)).read()\n    rows=json.loads(raw.decode("utf-8"))\n    candle=select_first_candle_at_or_after(rows,maturity)\n    candle_start=datetime.fromtimestamp(int(candle[0]),timezone.utc)\n    outcome_price=float(candle[4])\n    start_price=experience_start_spot_price(experience)\n    ret=outcome_price/start_price-1.0\n    source_hash=_h({"url":url,"product":product,"candle":candle})\n    source_ref=f"coinbase.exchange:{product}:candle:{int(candle[0])}"\n    o=build_outcome_observation(experience.asset,f"coinbase_spot_return_{int(horizon_seconds)}s_exact_interval",ret,candle_start.isoformat(),source_ref,source_hash)\n    if not verify_outcome_observation(o): raise RuntimeError("OCL-003 exact-horizon outcome verification failed")\n    return ExactHorizonCryptoOutcome(experience.experience_id,experience.asset,int(horizon_seconds),maturity.isoformat(),candle_start.isoformat(),start_price,outcome_price,ret,ret*100.0,source_ref,source_hash,o,True,True,False)\n'
TEST_SOURCE='import unittest,json\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome\nclass Resp:\n    def read(self): return json.dumps([[1787972520,99,102,100,101,12],[1787972460,98,101,99,100,10]]).encode()\ndef opener(req,timeout): return Resp()\nclass T(unittest.TestCase):\n    def test_exact(self):\n        e=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-29T02:00:00+00:00",condition_vector=(("coinbase","spot_price",100.0,"OBSERVED"),))\n        x=acquire_exact_coinbase_outcome(e,60,opener=opener)\n        print("[MATURITY]",x.matures_at); print("[CANDLE]",x.candle_start); print("[RETURN]",x.return_percent)\n        self.assertTrue(x.exact_interval); self.assertEqual(x.outcome_observation.outcome_type,"coinbase_spot_return_60s_exact_interval")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-187 deterministic first-Coinbase-minute-at/after-horizon outcome certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_187_crypto_exact_horizon_coinbase_outcome.py'; test=r/'test_oad_187_crypto_exact_horizon_coinbase_outcome.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-187 CRYPTO EXACT-HORIZON COINBASE OUTCOME INSTALLER"); print("="*118); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py', 'oad_183_crypto_experience_outcome_maturity_gate.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in ['qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py']:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_187_crypto_exact_horizon_coinbase_outcome import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-187 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
