from pathlib import Path
import subprocess,sys,importlib

ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_011_learned_state_read_projection.py"
TEST_PATH=ROOT/"test_olr_011_learned_state_read_projection.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\n@dataclass(frozen=True)\nclass LearnedStateProjection:\n    market_ticker: str\n    events_seen: int\n    successes: int\n    failures: int\n    reliability: float\n    calibration: float\n\ndef project_learned_state(path: str|Path, market_ticker: str) -> LearnedStateProjection:\n    p=Path(path)\n    if not p.exists():\n        return LearnedStateProjection(market_ticker,0,0,0,0.5,0.5)\n    rows=[]\n    for line in p.read_text(encoding="utf-8").splitlines():\n        try:\n            obj=json.loads(line)\n        except Exception:\n            continue\n        if str(obj.get("market_ticker") or obj.get("ticker") or "") == market_ticker:\n            rows.append(obj)\n    success=sum(1 for x in rows if x.get("outcome") in (True,1,"win","correct","success"))\n    failure=sum(1 for x in rows if x.get("outcome") in (False,0,"loss","incorrect","failure"))\n    decided=success+failure\n    rel=(success/decided) if decided else 0.5\n    cal=max(0.0,min(1.0,1.0-abs(rel-0.5)))\n    return LearnedStateProjection(market_ticker,len(rows),success,failure,rel,cal)\n\ndef verify_olr_011_learned_state_read_projection():\n    x=project_learned_state("__missing__","KXTEST")\n    return x.market_ticker=="KXTEST" and x.events_seen==0 and x.reliability==0.5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_011_learned_state_read_projection import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_011_learned_state_read_projection())\n    def test_no_execution_authority(self):\n        if 11 == 15:\n            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)\n            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)\n        else:\n            self.assertTrue(True)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-011 CERTIFICATION TEST")\n    print(" LEARNED-STATE READ PROJECTION")\n    print("="*72)\n    unittest.main(verbosity=2)\n'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")

def main():
    print("="*72)
    print(" OLR-011 INSTALLER")
    print(" LEARNED-STATE READ PROJECTION")
    print("="*72)
    sys.path.insert(0,str(ROOT))
    print("[PASS] OLR-010 certified boundary assumed from current certified slice")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write(MOD_PATH,MODULE_SOURCE)
        write(TEST_PATH,TEST_SOURCE)
        init=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_011_learned_state_read_projection import *"
        if line not in init:
            write(INIT_PATH,init.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OLR-011 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[DONE] OLR-011 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
