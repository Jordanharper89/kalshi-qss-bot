from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_177_CRYPTO_HISTORICAL_EXPERIENCE_CANDIDATE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass CryptoHistoricalExperienceCandidate:\n    experience_id:str\n    asset:str\n    snapshot_at:str\n    cohort_state:str\n    condition_vector:tuple\n    temporal_vector:tuple\n    evidence_state:str\n    consistency_state:str\n    market_native_metrics:int\n    independent_chain_metrics:int\n    comparable_temporal_metrics:int\n    evidence_hash:str\n    condition_hash:str\n    experience_hash:str\n    outcome_attached:bool=False\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef build_crypto_historical_experience_candidates(runtime_result):\n    changes_by_asset={}\n    for x in tuple(runtime_result.changes):\n        changes_by_asset.setdefault(str(x.asset),[]).append(x)\n    profiles={str(x.asset):x for x in tuple(runtime_result.profiles)}\n    out=[]\n    for asset in sorted(profiles):\n        p=profiles[asset]\n        changes=tuple(sorted(changes_by_asset.get(asset,()),key=lambda x:(x.source_family,x.metric_name)))\n        cond=tuple((\n            str(x.source_family),str(x.metric_name),float(x.current_value),str(x.current_condition)\n        ) for x in changes)\n        temporal=tuple((\n            str(x.source_family),str(x.metric_name),str(x.temporal_state),\n            None if x.absolute_change is None else float(x.absolute_change),\n            None if x.percent_change is None else float(x.percent_change),\n            bool(x.comparable_history_present),\n        ) for x in changes)\n        evidence_raw={\n            "asset":asset,\n            "evidence_state":str(p.evidence_state),\n            "consistency_state":str(p.consistency_state),\n            "market_native_metrics":int(p.market_native_metrics),\n            "independent_chain_metrics":int(p.independent_chain_metrics),\n        }\n        evidence_hash=_h(evidence_raw)\n        condition_hash=_h({"condition_vector":cond,"temporal_vector":temporal})\n        raw={\n            "asset":asset,"snapshot_at":str(runtime_result.snapshot_at),\n            "cohort_state":str(runtime_result.cohort_state),\n            "evidence_hash":evidence_hash,"condition_hash":condition_hash,\n            "outcome_attached":False,"probability":None,"direction":None,\n        }\n        experience_hash=_h(raw)\n        experience_id=f"crypto-exp:{asset}:{experience_hash[:24]}"\n        out.append(CryptoHistoricalExperienceCandidate(\n            experience_id,asset,str(runtime_result.snapshot_at),str(runtime_result.cohort_state),\n            cond,temporal,str(p.evidence_state),str(p.consistency_state),\n            int(p.market_native_metrics),int(p.independent_chain_metrics),\n            sum(1 for x in changes if x.comparable_history_present),\n            evidence_hash,condition_hash,experience_hash,False,None,None,False\n        ))\n    return tuple(out)\n\ndef verify_crypto_historical_experience_candidate(x):\n    if x.outcome_attached or x.probability is not None or x.direction is not None or x.execution_authority:\n        return False\n    evidence_hash=_h({\n        "asset":x.asset,"evidence_state":x.evidence_state,"consistency_state":x.consistency_state,\n        "market_native_metrics":x.market_native_metrics,"independent_chain_metrics":x.independent_chain_metrics,\n    })\n    condition_hash=_h({"condition_vector":x.condition_vector,"temporal_vector":x.temporal_vector})\n    experience_hash=_h({\n        "asset":x.asset,"snapshot_at":x.snapshot_at,"cohort_state":x.cohort_state,\n        "evidence_hash":evidence_hash,"condition_hash":condition_hash,\n        "outcome_attached":False,"probability":None,"direction":None,\n    })\n    return x.evidence_hash==evidence_hash and x.condition_hash==condition_hash and x.experience_hash==experience_hash\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_177_crypto_historical_experience_candidate import build_crypto_historical_experience_candidates,verify_crypto_historical_experience_candidate\nclass T(unittest.TestCase):\n    def test_candidate(self):\n        ch=SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",current_value=12,current_condition="ELEVATED",temporal_state="INCREASED",absolute_change=2,percent_change=20,comparable_history_present=True)\n        p=SimpleNamespace(asset="BTC",evidence_state="CROSS_SOURCE_PRESENT",consistency_state="NO_EXPLICIT_CONTRADICTION",market_native_metrics=3,independent_chain_metrics=7)\n        r=SimpleNamespace(snapshot_at="2026-08-29T02:00:00+00:00",cohort_state="FULL_COVERAGE",changes=(ch,),profiles=(p,))\n        x=build_crypto_historical_experience_candidates(r)[0]\n        print("[EXPERIENCE_ID]",x.experience_id)\n        print("[COMPARABLE]",x.comparable_temporal_metrics)\n        self.assertTrue(verify_crypto_historical_experience_candidate(x))\n        self.assertFalse(x.outcome_attached)\n        self.assertIsNone(x.probability)\n        self.assertIsNone(x.direction)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-177 deterministic outcome-pending crypto experience candidate certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_177_crypto_historical_experience_candidate.py'; test=r/'test_oad_177_crypto_historical_experience_candidate.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-177 CRYPTO HISTORICAL EXPERIENCE CANDIDATE INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_175_crypto_durable_temporal_intelligence_runtime.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_177_crypto_historical_experience_candidate import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-177 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
