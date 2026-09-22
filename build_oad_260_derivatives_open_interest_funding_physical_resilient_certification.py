
from __future__ import annotations
import ast, hashlib, os, subprocess, sys, textwrap
from pathlib import Path

BUILD_ID = 'OAD-260'
REVISION = 'OAD_260_DERIVATIVES_OPEN_INTEREST_FUNDING_PHYSICAL_RESILIENT_ACQUISITION_CERTIFICATION_V1'
TITLE = 'DERIVATIVES OPEN-INTEREST FUNDING PHYSICAL RESILIENT ACQUISITION CERTIFICATION'
MODULE_NAME = 'oad_260_derivatives_open_interest_funding_physical_resilient_certification.py'
TEST_NAME = 'test_oad_260_derivatives_open_interest_funding_physical_resilient_certification.py'
DEPENDENCIES = ['qseries_v2/oracle_adapters/independent/oad_256_crypto_derivatives_open_interest_funding_intelligence.py', 'qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py']
MODULE_SOURCE = '\nfrom dataclasses import dataclass\nimport json, urllib.request\nfrom .oad_256_crypto_derivatives_open_interest_funding_intelligence import acquire_derivatives_state\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation,verify_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nHYPERLIQUID_INFO="https://api.hyperliquid.xyz/info"\ndef _hyperliquid_info(timeout_seconds=20.0):\n    body=json.dumps({"type":"metaAndAssetCtxs"}).encode()\n    req=urllib.request.Request(HYPERLIQUID_INFO,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})\n    with urllib.request.urlopen(req,timeout=float(timeout_seconds)) as r: return json.loads(r.read().decode())\ndef acquire_hyperliquid_derivatives_state(asset="BTC",timeout_seconds=20.0):\n    d=_hyperliquid_info(timeout_seconds)\n    if not isinstance(d,list) or len(d)<2: raise RuntimeError("Hyperliquid meta/context response invalid")\n    meta,ctxs=d[0],d[1]; universe=(meta or {}).get("universe") or []\n    idx=next((i for i,x in enumerate(universe) if str(x.get("name") or "").upper()==str(asset).upper()),None)\n    if idx is None or idx>=len(ctxs): raise RuntimeError("Hyperliquid asset context unavailable")\n    c=ctxs[idx] or {}\n    payload={"symbol":str(asset).upper(),"mark_price":c.get("markPx"),"index_price":c.get("oraclePx"),"open_interest":c.get("openInterest"),"funding_rate":c.get("funding"),"volume_24h":c.get("dayNtlVlm"),"provider_path":"hyperliquid_metaAndAssetCtxs"}\n    if payload["open_interest"] is None or payload["funding_rate"] is None: raise RuntimeError("Hyperliquid derivatives fields missing")\n    return build_independent_crypto_observation(source_id="source.derivatives.hyperliquid."+str(asset).lower(),provider="hyperliquid_public_info",source_class="derivatives_state",subject=str(asset).upper(),observation_type="open_interest_funding",payload=payload)\n@dataclass(frozen=True,slots=True)\nclass DerivativesPhysicalCertification:\n    provider:str; symbol:str; open_interest:str; funding_rate:str; provenance_hash:str; primary_provider_succeeded:bool; fallback_used:bool; certified:bool; execution_authority:bool=False\ndef acquire_resilient_derivatives_state(symbol="BTCUSDT",timeout_seconds=20.0):\n    try:\n        return acquire_derivatives_state(symbol=symbol,timeout=timeout_seconds),True,False\n    except Exception as primary_error:\n        asset=str(symbol).upper()\n        if asset.endswith("USDT"): asset=asset[:-4]\n        try:\n            return acquire_hyperliquid_derivatives_state(asset,timeout_seconds),False,True\n        except Exception as fallback_error:\n            raise RuntimeError(f"all certified derivatives providers unavailable; primary={type(primary_error).__name__}; fallback={type(fallback_error).__name__}") from fallback_error\ndef certify_live_derivatives_state(symbol="BTCUSDT",timeout_seconds=20.0):\n    x,primary,fallback=acquire_resilient_derivatives_state(symbol,timeout_seconds)\n    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")\n    p=x.payload\n    if p.get("open_interest") is None or p.get("funding_rate") is None: raise RuntimeError("live derivatives state incomplete")\n    return DerivativesPhysicalCertification(x.provider,str(p.get("symbol") or symbol),str(p["open_interest"]),str(p["funding_rate"]),x.provenance_hash,primary,fallback,True,False)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_260_derivatives_open_interest_funding_physical_resilient_certification import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=certify_live_derivatives_state()\n  print("[PHYSICAL] provider=",r.provider); print("[PHYSICAL] symbol=",r.symbol); print("[PHYSICAL] open_interest=",r.open_interest); print("[PHYSICAL] funding_rate=",r.funding_rate); print("[PHYSICAL] primary_provider_succeeded=",r.primary_provider_succeeded); print("[PHYSICAL] fallback_used=",r.fallback_used)\n  self.assertTrue(r.certified); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-260 physical live resilient derivatives acquisition certified")\n'

def locate_root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"
    freeze=root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    kalshi=root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel in DEPENDENCIES:
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        print("[PASS] dependency verified:",rel)

    frozen={}
    for p,label in ((freeze,"Frozen OPH-023"),(kalshi,"Frozen Kalshi OAD-055")):
        if p.is_file():
            frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
