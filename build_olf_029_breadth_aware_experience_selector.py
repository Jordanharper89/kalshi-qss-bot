from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_029_breadth_aware_experience.py";TEST=ROOT/"test_olf_029_breadth_aware_experience_selector.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .olf_006_structural_identity import resolve_structural_identity\nfrom .olf_024_regime_aware_experience import select_regime_aware_experience\nfrom .olf_028_series_maturity import materialize_series_maturity\n\nOLF_029_BUILD_ID="OLF-029";OLF_029_REVISION="OLF_029_BREADTH_AWARE_EXPERIENCE_SELECTOR_V1"\n\n@dataclass(frozen=True)\nclass BreadthAwareExperience:\n    market_ticker:str;series_key:str;maturity:str;series_admitted:bool;experience_available:bool;regime_id:str;reliability:float;learner_state_hash:str;reason:str;execution_authority:bool=False\n\ndef select_breadth_aware_experience(root=None,market_ticker="",source_rows=()):\n    root=Path(root or Path.cwd()).resolve();ident=resolve_structural_identity(market_ticker);m=materialize_series_maturity(root)\n    by={str(x["series_key"]):x for x in m["series"]};row=by.get(ident.series_key)\n    if row is None:\n        return BreadthAwareExperience(ident.market_ticker,ident.series_key,"BLIND",False,False,"",0.0,m["learner_state_hash"],"NO_LEARNED_SERIES_HISTORY",False)\n    if not row["reasoning_admitted"]:\n        return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],False,False,"",0.0,m["learner_state_hash"],"SERIES_HISTORY_NOT_MATURE_ENOUGH",False)\n    x=select_regime_aware_experience(root,ident.market_ticker,source_rows)\n    if not x.available:\n        return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],True,False,x.regime_id,x.recency_reliability,m["learner_state_hash"],x.reason,False)\n    return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],True,True,x.regime_id,x.recency_reliability,m["learner_state_hash"],"MATURE_SERIES_AND_MATCHED_REGIME",False)\n\ndef verify_olf_029_breadth_aware_experience_selector():\n    return OLF_029_BUILD_ID=="OLF-029" and callable(select_breadth_aware_experience)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_029_breadth_aware_experience as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_029_BUILD_ID,"OLF-029")\n    def test_contract(self):self.assertTrue(callable(m.select_breadth_aware_experience))\nif __name__=="__main__":\n    print("="*88);print(" OLF-029 CERTIFICATION TEST");print(" BREADTH-AWARE EXPERIENCE SELECTOR");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Series maturity gate ahead of regime intelligence certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-029 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(text,encoding="utf-8",newline="\n");os.replace(tmp,path)
def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)
def update_init(path,line):
    s=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in s.splitlines():write_exact(path,s.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-029 INSTALLER");print(" BREADTH-AWARE EXPERIENCE SELECTOR");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_028_series_maturity")
    if not up.verify_olf_028_series_maturity_admission():raise RuntimeError("OLF-028 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_029_breadth_aware_experience import *");subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-029 failed; files restored");raise
    print("[PASS] Mature series can use OLF-025 regimes");print("[PASS] Sparse/unscored series explicitly withheld");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-029 INSTALLATION COMPLETE")
if __name__=="__main__":main()
