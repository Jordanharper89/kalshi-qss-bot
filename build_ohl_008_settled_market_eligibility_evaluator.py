from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD_PATH=PKG/"ohl_008_settled_market_eligibility_evaluator.py"
TEST_PATH=ROOT/"test_ohl_008_settled_market_eligibility_evaluator.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import find_historical_market_evidence\nfrom .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline\nfrom .ohl_004_temporal_leakage_guard import guard_historical_timeline\nfrom .ohl_005_historical_learning_candidate_gate import build_historical_learning_candidate\nfrom .ohl_007_historical_evidence_coverage_scanner import verify_ohl_007_historical_evidence_coverage_scanner\n\nOHL_008_BUILD_ID="OHL-008"\nOHL_008_REVISION="OHL_008_SETTLED_MARKET_ELIGIBILITY_EVALUATOR_V1"\n\n@dataclass(frozen=True)\nclass SettledMarketEligibility:\n    ticker:str\n    eligible:bool\n    reason:str\n    evidence_count:int\n    candidate_id:str\n\ndef _row_to_observation(m,ticker):\n    row=getattr(m,"row",{}) or {}\n    observed_at=(row.get("observed_at") or row.get("timestamp") or row.get("created_at")\n                 or row.get("event_ts") or row.get("received_at"))\n    if not observed_at:\n        return None\n    return {\n        "observation_id":str(getattr(m,"observation_id","")),\n        "market_id":str(ticker),\n        "observed_at":str(observed_at),\n        "payload":dict(row),\n    }\n\ndef evaluate_settled_market_eligibility(root,outcome,evidence_limit=50):\n    if not verify_ohl_007_historical_evidence_coverage_scanner():\n        raise RuntimeError("OHL-007 verification failed")\n    ticker=str(getattr(outcome,"ticker",""))\n    settled_at=str(getattr(outcome,"settlement_ts",""))\n    result=str(getattr(outcome,"result",""))\n    if not ticker or not settled_at or not result:\n        return SettledMarketEligibility(ticker,False,"MISSING_SETTLEMENT_IDENTITY",0,"")\n    matches=tuple(find_historical_market_evidence(Path(root).resolve(),ticker,limit=int(evidence_limit)))\n    observations=[]\n    for m in matches:\n        obs=_row_to_observation(m,ticker)\n        if obs is not None:observations.append(obs)\n    timeline=reconstruct_settled_market_timeline(ticker,settled_at,result,observations)\n    guard=guard_historical_timeline(timeline)\n    if not guard.admitted:\n        return SettledMarketEligibility(ticker,False,guard.reason,len(timeline.evidence),"")\n    candidate=build_historical_learning_candidate(timeline)\n    if candidate is None:\n        return SettledMarketEligibility(ticker,False,"CANDIDATE_REJECTED",len(timeline.evidence),"")\n    return SettledMarketEligibility(ticker,True,"ELIGIBLE",len(timeline.evidence),candidate.candidate_id)\n\ndef verify_ohl_008_settled_market_eligibility_evaluator():\n    x=SettledMarketEligibility("KX",False,"NO_PRE_SETTLEMENT_EVIDENCE",0,"")\n    return not x.eligible and x.evidence_count==0\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_historical_learning.ohl_008_settled_market_eligibility_evaluator import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ohl_008_settled_market_eligibility_evaluator())\n    def test_contract(self):\n        x=SettledMarketEligibility("KX",True,"ELIGIBLE",3,"abc")\n        self.assertTrue(x.eligible)\n\nif __name__=="__main__":\n    print("="*72);print(" OHL-008 CERTIFICATION TEST");print(" SETTLED MARKET ELIGIBILITY EVALUATOR");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Settled-market historical eligibility evaluator certified")\n    print("[DONE] OHL-008 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-008 INSTALLER")
    print(" SETTLED MARKET ELIGIBILITY EVALUATOR")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module('qseries_v2.oracle_historical_learning.ohl_007_historical_evidence_coverage_scanner')
    if getattr(up,'verify_ohl_007_historical_evidence_coverage_scanner')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OHL-007 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .ohl_008_settled_market_eligibility_evaluator import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-008 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OHL-008 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
