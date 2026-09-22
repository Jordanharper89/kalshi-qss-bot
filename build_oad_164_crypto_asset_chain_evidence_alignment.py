from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_164_CRYPTO_ASSET_CHAIN_EVIDENCE_ALIGNMENT_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nDIRECTION_ENABLED=False\n\nCHAIN_ASSET={"bitcoin":"BTC","ethereum":"ETH","solana":"SOL"}\n\n@dataclass(frozen=True,slots=True)\nclass CryptoAssetEvidenceAlignment:\n    asset:str\n    market_observations:tuple\n    chain_observations:tuple\n    market_source_present:bool\n    chain_source_present:bool\n    evidence_comparison_possible:bool\n    observation_time_span_seconds:float|None\n    direction:None=None\n    probability:None=None\n\ndef _dt(v):\n    try:\n        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n    except Exception:\n        return None\n\ndef align_crypto_asset_chain_evidence(cohort):\n    market={a:[] for a in ("BTC","ETH","SOL")}\n    chain={a:[] for a in ("BTC","ETH","SOL")}\n    for family,o in tuple(cohort.observations):\n        if family=="coinbase":\n            subject=str(getattr(o,"subject","")).upper()\n            for asset in market:\n                if subject.startswith(asset+"-"):\n                    market[asset].append(o); break\n        elif family in CHAIN_ASSET:\n            chain[CHAIN_ASSET[family]].append(o)\n    out=[]\n    for asset in ("BTC","ETH","SOL"):\n        all_obs=tuple(market[asset])+tuple(chain[asset])\n        times=[_dt(getattr(x,"observed_at",None)) for x in all_obs]\n        times=[x for x in times if x is not None]\n        span=(max(times)-min(times)).total_seconds() if len(times)>=2 else None\n        out.append(CryptoAssetEvidenceAlignment(asset,tuple(market[asset]),tuple(chain[asset]),bool(market[asset]),bool(chain[asset]),bool(market[asset]) and bool(chain[asset]),span,None,None))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_164_crypto_asset_chain_evidence_alignment import align_crypto_asset_chain_evidence\nclass T(unittest.TestCase):\n    def test_alignment(self):\n        obs=(("coinbase",SimpleNamespace(subject="BTC-USD",observed_at="2026-08-29T00:00:00+00:00")),("bitcoin",SimpleNamespace(subject="Bitcoin",observed_at="2026-08-29T00:00:02+00:00")),("solana",SimpleNamespace(subject="Solana",observed_at="2026-08-29T00:00:03+00:00")))\n        cohort=SimpleNamespace(observations=obs)\n        r=align_crypto_asset_chain_evidence(cohort)\n        btc=r[0]\n        print("[BTC_COMPARISON]",btc.evidence_comparison_possible); print("[BTC_SPAN]",btc.observation_time_span_seconds)\n        self.assertTrue(btc.evidence_comparison_possible); self.assertIsNone(btc.direction); self.assertIsNone(btc.probability)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-164 crypto asset-chain evidence alignment certified")\n'
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
    module=pkg/'oad_164_crypto_asset_chain_evidence_alignment.py'; test=r/'test_oad_164_crypto_asset_chain_evidence_alignment.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-164 CRYPTO ASSET-CHAIN EVIDENCE ALIGNMENT INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_163_crypto_live_multi_source_cohort.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_164_crypto_asset_chain_evidence_alignment import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-164 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
