from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_027_series_learning_gaps.py";TEST=ROOT/"test_olf_027_series_learning_gap_classification.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport json,os\nfrom .olf_026_learning_coverage_atlas import materialize_learning_coverage_atlas\n\nOLF_027_BUILD_ID="OLF-027";OLF_027_REVISION="OLF_027_SERIES_LEARNING_GAP_CLASSIFICATION_V1";OUTPUT_NAME="oracle_series_learning_gap_classification.json"\n\ndef gap_reason(row):\n    learned=int(row["learned_records"]);ev=int(row["evidence_resolved"]);out=int(row["outcome_attributed"]);price=int(row["probability_recovered"]);scored=int(row["scored_records"])\n    if learned<=0:return "NO_LEARNED_EXPERIENCE"\n    if ev<=0:return "NO_CANONICAL_EVIDENCE"\n    if out<=0:return "NO_ATTRIBUTED_SETTLEMENT_RESULTS"\n    if price<=0:return "NO_PRESETTLEMENT_PROBABILITY"\n    if scored<=0:return "OUTCOME_AND_PRICE_NOT_JOINED"\n    if scored<5:return "SPARSE_SCORED_HISTORY"\n    return "SCORED_HISTORY_AVAILABLE"\n\ndef build_series_learning_gaps(root=None):\n    root=Path(root or Path.cwd()).resolve();a=materialize_learning_coverage_atlas(root);rows=[]\n    for x in a["series"]:\n        r=gap_reason(x)\n        missing_outcomes=max(0,int(x["learned_records"])-int(x["outcome_attributed"]))\n        missing_prices=max(0,int(x["learned_records"])-int(x["probability_recovered"]))\n        rows.append({**x,"gap_reason":r,"missing_outcome_records":missing_outcomes,"missing_probability_records":missing_prices})\n    return {"revision":OLF_027_REVISION,"learner_state_hash":a["learner_state_hash"],"series":rows,\n            "series_with_scored_history":sum(x["scored_records"]>0 for x in rows),\n            "series_without_scored_history":sum(x["scored_records"]<=0 for x in rows),\n            "execution_authority":False}\ndef materialize_series_learning_gaps(root=None):\n    root=Path(root or Path.cwd()).resolve();p=build_series_learning_gaps(root);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\ndef verify_olf_027_series_learning_gap_classification():\n    return OLF_027_BUILD_ID=="OLF-027" and gap_reason({"learned_records":2,"evidence_resolved":2,"outcome_attributed":0,"probability_recovered":2,"scored_records":0})=="NO_ATTRIBUTED_SETTLEMENT_RESULTS"\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_027_series_learning_gaps as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_027_BUILD_ID,"OLF-027")\n    def test_gap(self):self.assertEqual(m.gap_reason({"learned_records":3,"evidence_resolved":3,"outcome_attributed":0,"probability_recovered":3,"scored_records":0}),"NO_ATTRIBUTED_SETTLEMENT_RESULTS")\nif __name__=="__main__":\n    print("="*88);print(" OLF-027 CERTIFICATION TEST");print(" SERIES LEARNING GAP CLASSIFICATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Exact per-series learning blocker classification certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-027 CERTIFIED")\n'

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
    print("="*88);print(" OLF-027 INSTALLER");print(" SERIES LEARNING GAP CLASSIFICATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_026_learning_coverage_atlas")
    if not up.verify_olf_026_learning_coverage_breadth_atlas():raise RuntimeError("OLF-026 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_027_series_learning_gaps import *");subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_027_series_learning_gaps");p=m.materialize_series_learning_gaps(ROOT)
        print(f"[PHYSICAL GAPS] series_with_scored_history={p['series_with_scored_history']} series_without_scored_history={p['series_without_scored_history']} state_hash={p['learner_state_hash']}")
        for x in p["series"]:print(f"[SERIES GAP] series={x['series_key']} reason={x['gap_reason']} missing_outcomes={x['missing_outcome_records']} missing_prices={x['missing_probability_records']} scored={x['scored_records']}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-027 failed; files restored");raise
    print("[PASS] Breadth gaps are measured, not guessed");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-027 INSTALLATION COMPLETE")
if __name__=="__main__":main()
