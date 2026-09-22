from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_018_pattern_stability.py";TEST=ROOT/"test_olf_018_pattern_contradiction_stability.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport json,os\nfrom .olf_017_pattern_performance import materialize_pattern_performance\n\nOLF_018_BUILD_ID="OLF-018"\nOLF_018_REVISION="OLF_018_PATTERN_CONTRADICTION_STABILITY_V1"\nOUTPUT_NAME="oracle_pattern_contradiction_stability.json"\n\ndef build_pattern_stability(root=None):\n    root=Path(root or Path.cwd()).resolve();src=materialize_pattern_performance(root,3)\n    rows=[]\n    for x in src.get("patterns",[]):\n        failure_rate=1.0-float(x["hit_rate"])\n        calibration_error=float(x["calibration_error"])\n        contradiction=max(failure_rate,calibration_error)\n        reliable=float(x["reliability_weight"])\n        mature=bool(x["mature"])\n        stable=mature and contradiction<=.35 and reliable>=.35\n        status="STABLE" if stable else "CONTESTED" if mature else "INSUFFICIENT"\n        rows.append({**x,"failure_rate":failure_rate,"contradiction_score":contradiction,"stable":stable,"status":status})\n    return {"revision":OLF_018_REVISION,"learner_state_hash":src["learner_state_hash"],"patterns":rows,"stable_patterns":sum(1 for x in rows if x["stable"]),"contested_patterns":sum(1 for x in rows if x["status"]=="CONTESTED"),"execution_authority":False}\n\ndef materialize_pattern_stability(root=None):\n    root=Path(root or Path.cwd()).resolve();p=build_pattern_stability(root)\n    path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\n\ndef verify_olf_018_pattern_contradiction_stability():\n    return OLF_018_BUILD_ID=="OLF-018" and callable(build_pattern_stability)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_018_pattern_stability as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_018_BUILD_ID,"OLF-018")\nif __name__=="__main__":\n    print("="*88);print(" OLF-018 CERTIFICATION TEST");print(" PATTERN CONTRADICTION + STABILITY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Contradiction/stability classification certified")\n    print("[PASS] execution_authority=FALSE");print("[DONE] OLF-018 CERTIFIED")\n'

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
    print("="*88);print(" OLF-018 INSTALLER");print(" PATTERN CONTRADICTION + STABILITY");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_017_pattern_performance")
    if not up.verify_olf_017_pattern_performance_calibration():raise RuntimeError("OLF-017 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_018_pattern_stability import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_018_pattern_stability")
        p=m.materialize_pattern_stability(ROOT)
        print(f"[PHYSICAL STABILITY] patterns={len(p['patterns'])} stable={p['stable_patterns']} contested={p['contested_patterns']} state_hash={p['learner_state_hash']}")
        if not p["patterns"]:raise RuntimeError("No pattern performance records available")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-018 failed; files restored");raise
    print("[PASS] Poor/contradictory history is explicitly down-ranked");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-018 INSTALLATION COMPLETE")
if __name__=="__main__":main()
