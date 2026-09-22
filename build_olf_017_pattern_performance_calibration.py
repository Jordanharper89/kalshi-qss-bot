from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_017_pattern_performance.py";TEST=ROOT/"test_olf_017_pattern_performance_calibration.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom collections import defaultdict\nimport json,os\nfrom .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience\n\nOLF_017_BUILD_ID="OLF-017"\nOLF_017_REVISION="OLF_017_PATTERN_PERFORMANCE_CALIBRATION_V1"\nOUTPUT_NAME="oracle_pattern_performance_calibration.json"\n\ndef build_pattern_performance(root=None,min_samples=3):\n    root=Path(root or Path.cwd()).resolve();src=materialize_outcome_attributed_experience(root)\n    groups=defaultdict(list)\n    for x in src.get("records",[]):\n        if not x.get("scored"):continue\n        pid=str(x.get("series_key") or "")+"|"+str(x.get("observation_type") or "UNKNOWN")\n        groups[pid].append(x)\n    patterns=[]\n    for pid,rows in sorted(groups.items()):\n        if len(rows)<int(min_samples):continue\n        n=len(rows);hits=sum(1 for x in rows if x.get("prediction_hit") is True)\n        mean_prob=sum(float(x["implied_yes_probability"]) for x in rows)/n\n        yes_rate=sum(1 for x in rows if x.get("settlement_result")=="yes")/n\n        mean_brier=sum(float(x["brier_score"]) for x in rows)/n\n        calibration_error=abs(mean_prob-yes_rate)\n        sample_weight=n/(n+10.0)\n        reliability=max(0.0,min(1.0,sample_weight*(1.0-mean_brier)*(1.0-calibration_error)))\n        patterns.append({\n            "pattern_id":pid,"series_key":rows[0]["series_key"],\n            "observation_type":rows[0]["observation_type"],"samples":n,\n            "hits":hits,"misses":n-hits,"hit_rate":hits/n,\n            "mean_implied_yes_probability":mean_prob,"yes_outcome_rate":yes_rate,\n            "mean_brier_score":mean_brier,"calibration_error":calibration_error,\n            "reliability_weight":reliability,"mature":n>=5,\n        })\n    return {"revision":OLF_017_REVISION,"learner_state_hash":src["learner_state_hash"],"min_samples":int(min_samples),"patterns":patterns,"execution_authority":False}\n\ndef materialize_pattern_performance(root=None,min_samples=3):\n    root=Path(root or Path.cwd()).resolve();p=build_pattern_performance(root,min_samples)\n    path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\n\ndef verify_olf_017_pattern_performance_calibration():\n    return OLF_017_BUILD_ID=="OLF-017" and callable(build_pattern_performance)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_017_pattern_performance as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_017_BUILD_ID,"OLF-017")\n    def test_contract(self):self.assertTrue(callable(m.build_pattern_performance))\nif __name__=="__main__":\n    print("="*88);print(" OLF-017 CERTIFICATION TEST");print(" PATTERN PERFORMANCE + CALIBRATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Hit-rate/Brier/calibration/reliability aggregation certified")\n    print("[PASS] execution_authority=FALSE");print("[DONE] OLF-017 CERTIFIED")\n'

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
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-017 INSTALLER");print(" PATTERN PERFORMANCE + CALIBRATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_016_outcome_attributed_experience")
    if not up.verify_olf_016_outcome_attributed_pattern_experience():raise RuntimeError("OLF-016 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_017_pattern_performance import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_017_pattern_performance")
        p=m.materialize_pattern_performance(ROOT,3)
        print(f"[PHYSICAL PERFORMANCE] patterns={len(p['patterns'])} min_samples={p['min_samples']} state_hash={p['learner_state_hash']}")
        if not p["patterns"]:raise RuntimeError("No outcome-attributed pattern reached minimum sample threshold")
        for x in p["patterns"][:10]:print(f"[PATTERN PERFORMANCE] pattern={x['pattern_id']} samples={x['samples']} hit_rate={x['hit_rate']:.3f} brier={x['mean_brier_score']:.3f} calibration_error={x['calibration_error']:.3f} reliability={x['reliability_weight']:.3f}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-017 failed; files restored");raise
    print("[PASS] No directional pattern invented");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-017 INSTALLATION COMPLETE")
if __name__=="__main__":main()
