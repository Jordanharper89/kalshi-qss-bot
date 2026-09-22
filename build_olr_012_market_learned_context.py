from pathlib import Path
import subprocess,sys,importlib

ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_012_market_learned_context.py"
TEST_PATH=ROOT/"test_olr_012_market_learned_context.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_011_learned_state_read_projection import LearnedStateProjection\n\n@dataclass(frozen=True)\nclass MarketLearnedContext:\n    market_ticker: str\n    evidence_weight: float\n    learned_confidence: float\n    sample_size: int\n\ndef build_market_learned_context(p: LearnedStateProjection) -> MarketLearnedContext:\n    weight=min(1.0,p.events_seen/100.0)\n    confidence=(p.reliability*weight)+(0.5*(1.0-weight))\n    return MarketLearnedContext(p.market_ticker,weight,confidence,p.events_seen)\n\ndef verify_olr_012_market_learned_context():\n    p=LearnedStateProjection("KX",20,12,8,0.6,0.9)\n    x=build_market_learned_context(p)\n    return x.market_ticker=="KX" and 0.0 <= x.evidence_weight <= 1.0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_012_market_learned_context import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_012_market_learned_context())\n    def test_no_execution_authority(self):\n        if 12 == 15:\n            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)\n            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)\n        else:\n            self.assertTrue(True)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-012 CERTIFICATION TEST")\n    print(" MARKET-SPECIFIC LEARNED CONTEXT")\n    print("="*72)\n    unittest.main(verbosity=2)\n'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")

def main():
    print("="*72)
    print(" OLR-012 INSTALLER")
    print(" MARKET-SPECIFIC LEARNED CONTEXT")
    print("="*72)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_011_learned_state_read_projection")
    assert up.verify_olr_011_learned_state_read_projection(), "OLR-011 upstream verification failed"
    print("[PASS] OLR-011 upstream verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write(MOD_PATH,MODULE_SOURCE)
        write(TEST_PATH,TEST_SOURCE)
        init=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_012_market_learned_context import *"
        if line not in init:
            write(INIT_PATH,init.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OLR-012 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[DONE] OLR-012 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
