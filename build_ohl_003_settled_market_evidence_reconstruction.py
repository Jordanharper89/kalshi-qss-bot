from pathlib import Path
import os,sys,subprocess,importlib,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_historical_learning"
MOD=PKG/"ohl_003_settled_market_evidence_reconstruction.py"
TEST=ROOT/"test_ohl_003_settled_market_evidence_reconstruction.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom .ohl_002_postgresql_historical_observation_read_boundary import verify_ohl_002_postgresql_historical_observation_read_boundary\n\nOHL_003_BUILD_ID="OHL-003"\nOHL_003_REVISION="OHL_003_SETTLED_MARKET_EVIDENCE_RECONSTRUCTION_V1"\n\n@dataclass(frozen=True)\nclass HistoricalObservation:\n    observation_id:str\n    market_id:str\n    observed_at:str\n    payload:dict\n\n@dataclass(frozen=True)\nclass SettledMarketTimeline:\n    market_id:str\n    settled_at:str\n    outcome:str\n    evidence:tuple\n    rejected_post_settlement:int\n\ndef _dt(v):\n    if isinstance(v,datetime):\n        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    s=str(v).replace("Z","+00:00")\n    x=datetime.fromisoformat(s)\n    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)\n\ndef reconstruct_settled_market_timeline(market_id,settled_at,outcome,observations):\n    if not verify_ohl_002_postgresql_historical_observation_read_boundary():\n        raise RuntimeError("OHL-002 verification failed")\n    cutoff=_dt(settled_at)\n    accepted=[]; rejected=0\n    for raw in observations:\n        o=raw if isinstance(raw,HistoricalObservation) else HistoricalObservation(\n            str(raw["observation_id"]),str(raw["market_id"]),str(raw["observed_at"]),dict(raw.get("payload") or {}))\n        if o.market_id != str(market_id):\n            continue\n        if _dt(o.observed_at) < cutoff:\n            accepted.append(o)\n        else:\n            rejected += 1\n    accepted.sort(key=lambda x:(_dt(x.observed_at),x.observation_id))\n    return SettledMarketTimeline(str(market_id),str(settled_at),str(outcome),tuple(accepted),rejected)\n\ndef verify_ohl_003_settled_market_evidence_reconstruction():\n    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[\n        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}},\n        {"observation_id":"2","market_id":"M","observed_at":"2026-01-03T00:00:00Z","payload":{}},\n    ])\n    return len(x.evidence)==1 and x.rejected_post_settlement==1 and x.outcome=="YES"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ohl_003_settled_market_evidence_reconstruction())\n    def test_post_settlement_excluded(self):\n        x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[\n          {"observation_id":"x","market_id":"M","observed_at":"2026-01-02T00:00:00Z","payload":{}}])\n        self.assertEqual(len(x.evidence),0)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OHL-003 CERTIFICATION TEST")\n    print(" SETTLED MARKET EVIDENCE RECONSTRUCTION")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Settled Market Evidence Reconstruction certified")\n    print("[DONE] OHL-003 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OHL-003 INSTALLER")
    print(" SETTLED MARKET EVIDENCE RECONSTRUCTION")
    print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_historical_learning.ohl_002_postgresql_historical_observation_read_boundary")
    if getattr(up,"verify_ohl_002_postgresql_historical_observation_read_boundary")() is not True:
        raise RuntimeError("Certified OHL-002 upstream verification failed")
    print("[PASS] Certified OHL-002 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .ohl_003_settled_market_evidence_reconstruction import *"
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
        print("[ROLLBACK] OHL-003 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OHL-003 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
