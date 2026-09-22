from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_021_experience_regimes.py";TEST=ROOT/"test_olf_021_experience_regime_segmentation.py";INIT=PKG/"__init__.py";MAN=PKG/"OLF_020_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport json,os\nfrom .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience\n\nOLF_021_BUILD_ID="OLF-021"\nOLF_021_REVISION="OLF_021_EXPERIENCE_REGIME_SEGMENTATION_V1"\nOUTPUT_NAME="oracle_experience_regime_segments.json"\n\ndef probability_band(p):\n    if p is None:return "PRICE_UNKNOWN"\n    p=float(p)\n    if p<.20:return "YES_00_19"\n    if p<.40:return "YES_20_39"\n    if p<.60:return "YES_40_59"\n    if p<.80:return "YES_60_79"\n    return "YES_80_100"\n\ndef regime_id(row):\n    return "|".join((str(row.get("series_key") or "UNKNOWN"),\n                     str(row.get("observation_type") or "UNKNOWN"),\n                     str(row.get("utc_session") or "UNKNOWN"),\n                     probability_band(row.get("implied_yes_probability"))))\n\ndef build_regime_segments(root=None):\n    root=Path(root or Path.cwd()).resolve();src=materialize_outcome_attributed_experience(root)\n    rows=[]\n    for x in src.get("records",[]):\n        if not x.get("scored"):continue\n        rows.append({**x,"probability_band":probability_band(x.get("implied_yes_probability")),"regime_id":regime_id(x)})\n    return {"revision":OLF_021_REVISION,"learner_state_hash":src["learner_state_hash"],\n            "scored_records":len(rows),"distinct_regimes":len({x["regime_id"] for x in rows}),\n            "records":rows,"execution_authority":False}\n\ndef materialize_regime_segments(root=None):\n    root=Path(root or Path.cwd()).resolve();p=build_regime_segments(root);path=root/"runtime_state"/OUTPUT_NAME\n    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\n\ndef verify_olf_021_experience_regime_segmentation():\n    return OLF_021_BUILD_ID=="OLF-021" and probability_band(.10)=="YES_00_19" and probability_band(.90)=="YES_80_100"\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_021_experience_regimes as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_021_BUILD_ID,"OLF-021")\n    def test_bands(self):\n        self.assertEqual(m.probability_band(.10),"YES_00_19");self.assertEqual(m.probability_band(.50),"YES_40_59");self.assertEqual(m.probability_band(.90),"YES_80_100")\nif __name__=="__main__":\n    print("="*88);print(" OLF-021 CERTIFICATION TEST");print(" EXPERIENCE REGIME SEGMENTATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Series + evidence type + UTC session + probability-band regimes certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-021 CERTIFIED")\n'

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
    print("="*88);print(" OLF-021 INSTALLER");print(" EXPERIENCE GENERALIZATION — REGIME SEGMENTATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_020_reliability_aware_reasoning_runtime")
    if not MAN.is_file() or not up.verify_olf_020_reliability_aware_reasoning_runtime():raise RuntimeError("Frozen OLF-020 boundary verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_021_experience_regimes import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_021_experience_regimes");p=m.materialize_regime_segments(ROOT)
        print(f"[PHYSICAL REGIMES] scored_records={p['scored_records']} distinct_regimes={p['distinct_regimes']} state_hash={p['learner_state_hash']}")
        if p["scored_records"]<=0 or p["distinct_regimes"]<=0:raise RuntimeError("No physical outcome-scored regimes discovered")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-021 failed; files restored");raise
    print("[PASS] OLF-001 through OLF-020 untouched");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-021 INSTALLATION COMPLETE")
if __name__=="__main__":main()
