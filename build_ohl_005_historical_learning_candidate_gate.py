from pathlib import Path
import os,sys,subprocess,importlib,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD=PKG/"ohl_005_historical_learning_candidate_gate.py"
TEST=ROOT/"test_ohl_005_historical_learning_candidate_gate.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .ohl_004_temporal_leakage_guard import guard_historical_timeline,verify_ohl_004_temporal_leakage_guard\n\nOHL_005_BUILD_ID="OHL-005"\nOHL_005_REVISION="OHL_005_HISTORICAL_LEARNING_CANDIDATE_GATE_V1"\n\n@dataclass(frozen=True)\nclass HistoricalLearningCandidate:\n    candidate_id:str\n    market_id:str\n    outcome:str\n    settled_at:str\n    evidence_ids:tuple\n    admission_reason:str\n    execution_authority:bool=False\n\ndef build_historical_learning_candidate(timeline):\n    if not verify_ohl_004_temporal_leakage_guard():\n        raise RuntimeError("OHL-004 verification failed")\n    guard=guard_historical_timeline(timeline)\n    if not guard.admitted:\n        return None\n    evidence_ids=tuple(o.observation_id for o in timeline.evidence)\n    payload={"market_id":timeline.market_id,"outcome":timeline.outcome,\n             "settled_at":timeline.settled_at,"evidence_ids":evidence_ids}\n    cid=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return HistoricalLearningCandidate(cid,timeline.market_id,timeline.outcome,timeline.settled_at,\n                                       evidence_ids,"TEMPORALLY_CLEAN_SETTLED_HISTORY",False)\n\ndef verify_ohl_005_historical_learning_candidate_gate():\n    from .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline\n    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[\n        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}\n    ])\n    c=build_historical_learning_candidate(x)\n    return c is not None and len(c.candidate_id)==64 and not c.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_historical_learning.ohl_005_historical_learning_candidate_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ohl_005_historical_learning_candidate_gate())\n    def test_candidate_deterministic(self):\n        from qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline\n        x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[\n          {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}])\n        self.assertEqual(build_historical_learning_candidate(x).candidate_id,\n                         build_historical_learning_candidate(x).candidate_id)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OHL-005 CERTIFICATION TEST")\n    print(" HISTORICAL LEARNING CANDIDATE GATE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Historical Learning Candidate Gate certified")\n    print("[DONE] OHL-005 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-005 INSTALLER")
    print(" HISTORICAL LEARNING CANDIDATE GATE")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_historical_learning.ohl_004_temporal_leakage_guard")
    if getattr(up,"verify_ohl_004_temporal_leakage_guard")() is not True:
        raise RuntimeError("Certified OHL-004 upstream verification failed")
    print("[PASS] Certified OHL-004 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .ohl_005_historical_learning_candidate_gate import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OHL-005 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OHL-005 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
