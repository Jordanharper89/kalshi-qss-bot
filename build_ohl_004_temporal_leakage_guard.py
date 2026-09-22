from pathlib import Path
import os,sys,subprocess,importlib,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD=PKG/"ohl_004_temporal_leakage_guard.py"
TEST=ROOT/"test_ohl_004_temporal_leakage_guard.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom .ohl_003_settled_market_evidence_reconstruction import SettledMarketTimeline,verify_ohl_003_settled_market_evidence_reconstruction\n\nOHL_004_BUILD_ID="OHL-004"\nOHL_004_REVISION="OHL_004_TEMPORAL_LEAKAGE_GUARD_V1"\n\n@dataclass(frozen=True)\nclass LeakageGuardResult:\n    admitted:bool\n    reason:str\n    evidence_count:int\n\ndef _dt(v):\n    s=str(v).replace("Z","+00:00")\n    x=datetime.fromisoformat(s)\n    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)\n\ndef guard_historical_timeline(timeline:SettledMarketTimeline):\n    if not verify_ohl_003_settled_market_evidence_reconstruction():\n        raise RuntimeError("OHL-003 verification failed")\n    if not timeline.outcome:\n        return LeakageGuardResult(False,"MISSING_SETTLED_OUTCOME",len(timeline.evidence))\n    if not timeline.evidence:\n        return LeakageGuardResult(False,"NO_PRE_SETTLEMENT_EVIDENCE",0)\n    cutoff=_dt(timeline.settled_at)\n    if any(_dt(o.observed_at) >= cutoff for o in timeline.evidence):\n        return LeakageGuardResult(False,"POST_SETTLEMENT_LEAKAGE",len(timeline.evidence))\n    return LeakageGuardResult(True,"TEMPORALLY_CLEAN",len(timeline.evidence))\n\ndef verify_ohl_004_temporal_leakage_guard():\n    from .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline\n    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[\n        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}\n    ])\n    g=guard_historical_timeline(x)\n    return g.admitted and g.reason=="TEMPORALLY_CLEAN"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_historical_learning.ohl_004_temporal_leakage_guard import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ohl_004_temporal_leakage_guard())\n    def test_empty_rejected(self):\n        from qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import SettledMarketTimeline\n        g=guard_historical_timeline(SettledMarketTimeline("M","2026-01-02T00:00:00Z","YES",tuple(),0))\n        self.assertFalse(g.admitted)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OHL-004 CERTIFICATION TEST")\n    print(" TEMPORAL LEAKAGE GUARD")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Temporal Leakage Guard certified")\n    print("[DONE] OHL-004 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-004 INSTALLER")
    print(" TEMPORAL LEAKAGE GUARD")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction")
    if getattr(up,"verify_ohl_003_settled_market_evidence_reconstruction")() is not True:
        raise RuntimeError("Certified OHL-003 upstream verification failed")
    print("[PASS] Certified OHL-003 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .ohl_004_temporal_leakage_guard import *"
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
        print("[ROLLBACK] OHL-004 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OHL-004 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
