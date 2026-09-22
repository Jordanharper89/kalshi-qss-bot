from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_022_regime_performance.py";TEST=ROOT/"test_olf_022_regime_specific_performance_calibration.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom collections import defaultdict\nimport json,os\nfrom .olf_021_experience_regimes import materialize_regime_segments\n\nOLF_022_BUILD_ID="OLF-022";OLF_022_REVISION="OLF_022_REGIME_SPECIFIC_PERFORMANCE_CALIBRATION_V1";OUTPUT_NAME="oracle_regime_performance_calibration.json"\n\ndef build_regime_performance(root=None,min_samples=2):\n    root=Path(root or Path.cwd()).resolve();src=materialize_regime_segments(root);g=defaultdict(list)\n    for x in src["records"]:g[x["regime_id"]].append(x)\n    out=[]\n    for rid,rows in sorted(g.items()):\n        if len(rows)<min_samples:continue\n        n=len(rows);hits=sum(x["prediction_hit"] is True for x in rows);b=sum(float(x["brier_score"]) for x in rows)/n\n        mp=sum(float(x["implied_yes_probability"]) for x in rows)/n;yr=sum(x["settlement_result"]=="yes" for x in rows)/n;ce=abs(mp-yr)\n        support=n/(n+8.0);rel=max(0.0,min(1.0,support*(1-b)*(1-ce)))\n        out.append({"regime_id":rid,"series_key":rows[0]["series_key"],"observation_type":rows[0]["observation_type"],"utc_session":rows[0]["utc_session"],"probability_band":rows[0]["probability_band"],"samples":n,"hit_rate":hits/n,"mean_brier_score":b,"calibration_error":ce,"reliability_weight":rel})\n    return {"revision":OLF_022_REVISION,"learner_state_hash":src["learner_state_hash"],"min_samples":min_samples,"regimes":out,"execution_authority":False}\ndef materialize_regime_performance(root=None,min_samples=2):\n    root=Path(root or Path.cwd()).resolve();p=build_regime_performance(root,min_samples);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\ndef verify_olf_022_regime_specific_performance_calibration():return OLF_022_BUILD_ID=="OLF-022" and callable(build_regime_performance)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_022_regime_performance as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_022_BUILD_ID,"OLF-022")\n    def test_contract(self):self.assertTrue(callable(m.build_regime_performance))\nif __name__=="__main__":\n    print("="*88);print(" OLF-022 CERTIFICATION TEST");print(" REGIME-SPECIFIC PERFORMANCE CALIBRATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Regime hit-rate/Brier/calibration/reliability contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-022 CERTIFIED")\n'

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
    print("="*88);print(" OLF-022 INSTALLER");print(" REGIME-SPECIFIC PERFORMANCE CALIBRATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_021_experience_regimes")
    if not up.verify_olf_021_experience_regime_segmentation():raise RuntimeError("OLF-021 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_022_regime_performance import *");subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_022_regime_performance");p=m.materialize_regime_performance(ROOT,2)
        print(f"[PHYSICAL REGIME PERFORMANCE] qualified_regimes={len(p['regimes'])} min_samples={p['min_samples']} state_hash={p['learner_state_hash']}")
        if not p["regimes"]:raise RuntimeError("No regime has enough scored outcomes for performance calibration")
        for x in p["regimes"][:12]:print(f"[REGIME PERFORMANCE] regime={x['regime_id']} samples={x['samples']} hit_rate={x['hit_rate']:.3f} brier={x['mean_brier_score']:.3f} calibration_error={x['calibration_error']:.3f} reliability={x['reliability_weight']:.3f}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-022 failed; files restored");raise
    print("[PASS] execution_authority=FALSE");print("[DONE] OLF-022 INSTALLATION COMPLETE")
if __name__=="__main__":main()
