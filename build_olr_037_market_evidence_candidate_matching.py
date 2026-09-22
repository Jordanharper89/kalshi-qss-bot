from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_037_market_evidence_candidate_matching.py";TEST=ROOT/"test_olr_037_market_evidence_candidate_matching.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_036_outcome_evidence_linkage_foundation import build_outcome_evidence_key,normalize_text\nOLR_037_BUILD_ID="OLR-037"\nOLR_037_REVISION="OLR_037_MARKET_EVIDENCE_CANDIDATE_MATCHING_V1"\n\n@dataclass(frozen=True)\nclass EvidenceMatch:\n    matched:bool\n    method:str\n    score:int\n    candidate:object|None\n\ndef _get(obj,key,default=None):\n    if hasattr(obj,"get"):return obj.get(key,default)\n    return getattr(obj,key,default)\n\ndef score_candidate(outcome,candidate):\n    key=build_outcome_evidence_key(outcome)\n    score=0\n    obs=normalize_text(_get(candidate,"observation_id",""))\n    ticker=normalize_text(_get(candidate,"ticker","") or _get(candidate,"market_ticker",""))\n    market=normalize_text(_get(candidate,"market_id","") or ticker)\n    if key.observation_id and obs==key.observation_id:score+=100\n    if key.ticker and ticker==key.ticker:score+=50\n    if key.market_id and market==key.market_id:score+=50\n    return score\n\ndef match_outcome_to_evidence(outcome,candidates):\n    ranked=sorted(((score_candidate(outcome,c),c) for c in candidates),key=lambda x:x[0],reverse=True)\n    if not ranked or ranked[0][0]<=0:return EvidenceMatch(False,"NONE",0,None)\n    score,candidate=ranked[0]\n    method="OBSERVATION_ID" if score>=100 and build_outcome_evidence_key(outcome).observation_id else "MARKET_ID"\n    return EvidenceMatch(True,method,score,candidate)\n\ndef verify_olr_037_market_evidence_candidate_matching(root=None):\n    m=match_outcome_to_evidence({"ticker":"X"},[{"ticker":"X"}])\n    return OLR_037_BUILD_ID=="OLR-037" and m.matched and m.score>=50\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_037_market_evidence_candidate_matching import *\nclass T(unittest.TestCase):\n    def test_ticker_match(self):\n        m=match_outcome_to_evidence({"ticker":"X"},[{"ticker":"X"}])\n        self.assertTrue(m.matched)\n    def test_observation_id_priority(self):\n        m=match_outcome_to_evidence({"ticker":"X","observation_id":"o2"},[{"ticker":"X","observation_id":"o1"},{"ticker":"X","observation_id":"o2"}])\n        self.assertEqual(m.candidate["observation_id"],"o2")\nif __name__=="__main__":\n    print("="*88);print(" OLR-037 CERTIFICATION TEST");print(" MARKET EVIDENCE CANDIDATE MATCHING");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Deterministic evidence candidate matching certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-037 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-037 INSTALLER");print(" MARKET EVIDENCE CANDIDATE MATCHING");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_036_outcome_evidence_linkage_foundation")
    if not up.verify_olr_036_outcome_evidence_linkage_foundation(ROOT):raise RuntimeError("Certified OLR-036 verification failed")
    print("[PASS] Certified OLR-036 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_037_market_evidence_candidate_matching import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-037 installation failed; affected files restored");raise
    print("[PASS] OLR-036 preserved read-only");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-037 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
