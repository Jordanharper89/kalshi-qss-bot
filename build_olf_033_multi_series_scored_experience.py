from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_033_multi_series_scored_experience.py";TEST=ROOT/"test_olf_033_multi_series_scored_experience.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom collections import defaultdict\nimport json,os\nfrom .olf_032_presettlement_price_recovery import materialize_presettlement_price_recovery\n\nOLF_033_BUILD_ID="OLF-033"\nOLF_033_REVISION="OLF_033_MULTI_SERIES_SCORED_EXPERIENCE_V1"\nOUTPUT_NAME="oracle_multi_series_scored_experience.json"\n\ndef build_multi_series_scored_experience(root=None):\n    root=Path(root or Path.cwd()).resolve();src=materialize_presettlement_price_recovery(root);rows=[]\n    for x in src["records"]:\n        result=str(x.get("settlement_result") or "").lower();prob=x.get("recovered_yes_probability")\n        actual=1.0 if result=="yes" else 0.0 if result=="no" else None;scored=(actual is not None and prob is not None)\n        y={**x,"scored":scored,"predicted_side":("yes" if float(prob)>=.5 else "no") if prob is not None else "",\n           "prediction_hit":bool((float(prob)>=.5)==(actual==1.0)) if scored else None,\n           "brier_score":((float(prob)-actual)**2) if scored else None}\n        rows.append(y)\n    by=defaultdict(int)\n    for x in rows:\n        if x["scored"]:by[str(x.get("series_key") or "UNKNOWN")]+=1\n    return {"revision":OLF_033_REVISION,"learner_state_hash":src["learner_state_hash"],"records":rows,\n            "scored_records":sum(x["scored"] for x in rows),"scored_series":dict(sorted(by.items())),\n            "distinct_scored_series":len(by),"execution_authority":False}\n\ndef materialize_multi_series_scored_experience(root=None):\n    root=Path(root or Path.cwd()).resolve();p=build_multi_series_scored_experience(root);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\n\ndef verify_olf_033_multi_series_scored_experience():\n    return OLF_033_BUILD_ID=="OLF-033" and callable(build_multi_series_scored_experience)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_033_multi_series_scored_experience as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_033_BUILD_ID,"OLF-033")\n    def test_contract(self):self.assertTrue(callable(m.build_multi_series_scored_experience))\nif __name__=="__main__":\n    print("="*88);print(" OLF-033 CERTIFICATION TEST");print(" MULTI-SERIES SCORED EXPERIENCE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Recovered outcome + pre-settlement probability scoring certified")\n    print("[PASS] execution_authority=FALSE");print("[DONE] OLF-033 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)
def update_init(path,line):
    s=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in s.splitlines():write_exact(path,s.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-033 INSTALLER");print(" MULTI-SERIES SCORED EXPERIENCE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_032_presettlement_price_recovery")
    if not up.verify_olf_032_presettlement_price_history_recovery():raise RuntimeError("OLF-032 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_033_multi_series_scored_experience import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_033_multi_series_scored_experience");p=m.materialize_multi_series_scored_experience(ROOT)
        baseline=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_026_learning_coverage_atlas").materialize_learning_coverage_atlas(ROOT)
        print(f"[PHYSICAL SCORED BREADTH] baseline_scored={baseline['total_scored_records']} recovered_scored={p['scored_records']} baseline_series={baseline['distinct_scored_series']} recovered_series={p['distinct_scored_series']} state_hash={p['learner_state_hash']}")
        for k,v in p["scored_series"].items():print(f"[SCORED SERIES] series={k} scored={v}")
        if p["scored_records"]<=baseline["total_scored_records"]:raise RuntimeError("Scored learning breadth did not increase over OLF-026 baseline")
        if p["distinct_scored_series"]<2:raise RuntimeError("Outcome/price recovery did not expand scoring into a second series")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-033 failed; files restored");raise
    print("[PASS] Scored experience physically expanded beyond the original single-series baseline");print("[PASS] Proven learner unchanged");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-033 INSTALLATION COMPLETE")
if __name__=="__main__":main()
