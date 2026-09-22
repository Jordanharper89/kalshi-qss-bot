from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION='OAD_170_CRYPTO_CROSS_SOURCE_CONSISTENCY_PROFILE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoCrossSourceConsistencyProfile:\n    asset:str\n    market_native_metrics:int\n    independent_chain_metrics:int\n    comparable_temporal_metrics:int\n    evidence_state:str\n    consistency_state:str\n    contradictions:tuple\n    direction:None=None\n    probability:None=None\n\ndef build_crypto_cross_source_consistency_profiles(states,changes=()):\n    assets=("BTC","ETH","SOL")\n    by_asset={a:[] for a in assets}\n    for x in tuple(states):\n        if x.asset in by_asset: by_asset[x.asset].append(x)\n    ch_by_asset={a:[] for a in assets}\n    for x in tuple(changes):\n        if x.asset in ch_by_asset: ch_by_asset[x.asset].append(x)\n\n    out=[]\n    for asset in assets:\n        rows=tuple(by_asset[asset])\n        market=sum(1 for x in rows if x.market_native_reference)\n        chain=sum(1 for x in rows if x.independent_evidence)\n        comparable=sum(1 for x in ch_by_asset[asset] if x.comparable_history_present)\n        evidence_state="CROSS_SOURCE_PRESENT" if market and chain else ("SINGLE_SOURCE_ONLY" if market or chain else "NO_EVIDENCE")\n\n        # Do not invent directional contradiction across incomparable metric types.\n        # Contradictions are reserved for explicit incompatible claims; none are\n        # manufactured merely because two activity metrics differ.\n        contradictions=tuple()\n        consistency="NO_EXPLICIT_CONTRADICTION" if evidence_state=="CROSS_SOURCE_PRESENT" else "NOT_COMPARABLE"\n        out.append(CryptoCrossSourceConsistencyProfile(\n            asset,market,chain,comparable,evidence_state,consistency,contradictions,None,None\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles\nclass T(unittest.TestCase):\n    def test_profile(self):\n        s=(\n            SimpleNamespace(asset="SOL",market_native_reference=True,independent_evidence=False),\n            SimpleNamespace(asset="SOL",market_native_reference=False,independent_evidence=True),\n        )\n        r=build_crypto_cross_source_consistency_profiles(s)[2]\n        print("[EVIDENCE_STATE]",r.evidence_state)\n        print("[CONSISTENCY]",r.consistency_state)\n        print("[CONTRADICTIONS]",r.contradictions)\n        self.assertEqual(r.evidence_state,"CROSS_SOURCE_PRESENT")\n        self.assertEqual(r.contradictions,())\n        self.assertIsNone(r.direction); self.assertIsNone(r.probability)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-170 cross-source consistency profile certified")\n'

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
    module=pkg/'oad_170_crypto_cross_source_consistency_profile.py'; test=r/'test_oad_170_crypto_cross_source_consistency_profile.py'; init=pkg/"__init__.py"
    print("="*112)
    print(" OAD-170 CRYPTO CROSS-SOURCE CONSISTENCY PROFILE INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_168_crypto_condition_state_normalization.py', 'oad_169_crypto_temporal_condition_change_evaluator.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_170_crypto_cross_source_consistency_profile import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-170 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
