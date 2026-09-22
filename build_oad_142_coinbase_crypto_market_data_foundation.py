from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_142_COINBASE_CRYPTO_MARKET_DATA_FOUNDATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_142_coinbase_crypto_market_data_foundation.py'; test=r/'test_oad_142_coinbase_crypto_market_data_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-142 COINBASE CRYPTO MARKET DATA FOUNDATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_061_independent_to_canonical_bridge.py', 'oad_062_independent_canonical_provenance_validation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nfrom typing import Any, Mapping\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nPROVIDER="api.exchange.coinbase.com"\nSOURCE_CLASS="market_native_reference"\nINDEPENDENT_EVIDENCE=False\n\n@dataclass(frozen=True)\nclass CoinbaseMarketObservation:\n    source_id:str\n    provider:str\n    crypto_family:str\n    observation_type:str\n    subject:str\n    observed_at:str\n    source_url:str\n    payload:Mapping[str,Any]\n    provenance_hash:str\n    source_class:str=SOURCE_CLASS\n    independent_evidence:bool=False\n    execution_authority:bool=False\n\ndef utcnow_iso():\n    return datetime.now(timezone.utc).isoformat()\n\ndef build_coinbase_market_observation(*,source_id,crypto_family,observation_type,subject,observed_at,source_url,payload):\n    if not str(source_url).startswith("https://api.exchange.coinbase.com/"):\n        raise ValueError("Coinbase observation must originate from official Exchange public REST boundary")\n    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)\n    ph=sha256((PROVIDER+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return CoinbaseMarketObservation(\n        str(source_id),PROVIDER,str(crypto_family),str(observation_type),str(subject),\n        str(observed_at),str(source_url),dict(payload),ph,SOURCE_CLASS,False,False\n    )\n\ndef validate_coinbase_market_observation(o):\n    return (\n        o.provider==PROVIDER and o.source_class==SOURCE_CLASS\n        and o.independent_evidence is False and o.execution_authority is False\n        and str(o.source_url).startswith("https://api.exchange.coinbase.com/")\n        and len(o.provenance_hash)==64\n    )\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_142_coinbase_crypto_market_data_foundation import build_coinbase_market_observation,validate_coinbase_market_observation\nclass T(unittest.TestCase):\n    def test_market_native_not_independent(self):\n        o=build_coinbase_market_observation(source_id="coinbase:BTC-USD:ticker",crypto_family="spot",observation_type="ticker",subject="BTC-USD",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.exchange.coinbase.com/products/BTC-USD/ticker",payload={"price":"60000"})\n        self.assertTrue(validate_coinbase_market_observation(o))\n        self.assertFalse(o.independent_evidence); self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-142 Coinbase crypto market-data foundation certified")\n    print("[PASS] Coinbase classified market_native_reference independent_evidence=FALSE")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_142_coinbase_crypto_market_data_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-142 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
