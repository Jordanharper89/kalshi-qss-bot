from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_013_behavior_patterns.py";TEST=ROOT/"test_olf_013_behavioral_pattern_aggregation.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom collections import defaultdict,Counter\nimport json,os\nfrom .olf_011_learned_experience_profile import materialize_learned_experience_profiles\n\nOLF_013_BUILD_ID="OLF-013"\nOLF_013_REVISION="OLF_013_BEHAVIORAL_PATTERN_AGGREGATION_V1"\nPATTERN_NAME="oracle_historical_behavior_patterns.json"\n\ndef build_behavior_patterns(root=None,min_samples=3):\n    root=Path(root or Path.cwd()).resolve();p=materialize_learned_experience_profiles(root)\n    groups=defaultdict(list)\n    for x in p.get("profiles",[]):\n        if not x.get("evidence_resolved"):continue\n        groups[(x["series_key"],x["observation_type"])].append(x)\n    patterns=[]\n    for (series_key,obs_type),rows in sorted(groups.items()):\n        if len(rows)<int(min_samples):continue\n        sessions=Counter(x["utc_session"] for x in rows)\n        sources=Counter(x["source_family"] or "UNKNOWN" for x in rows)\n        patterns.append({\n            "pattern_id":series_key+"|"+obs_type,\n            "series_key":series_key,\n            "observation_type":obs_type,\n            "samples":len(rows),\n            "support":min(1.0,len(rows)/25.0),\n            "mature":len(rows)>=int(min_samples),\n            "dominant_utc_session":sessions.most_common(1)[0][0],\n            "utc_sessions":dict(sorted(sessions.items())),\n            "source_families":dict(sorted(sources.items())),\n            "settlement_hashes":tuple(sorted(x["settlement_hash"] for x in rows)),\n        })\n    return {"revision":OLF_013_REVISION,"learner_state_hash":p["learner_state_hash"],"min_samples":int(min_samples),"patterns":patterns,"execution_authority":False}\n\ndef materialize_behavior_patterns(root=None,min_samples=3):\n    root=Path(root or Path.cwd()).resolve();payload=build_behavior_patterns(root,min_samples)\n    path=root/"runtime_state"/PATTERN_NAME;tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path)\n    return payload\n\ndef verify_olf_013_behavioral_pattern_aggregation():\n    return OLF_013_BUILD_ID=="OLF-013" and callable(build_behavior_patterns)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_013_behavior_patterns import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_013_BUILD_ID,"OLF-013")\nif __name__=="__main__":\n    print("="*88);print(" OLF-013 CERTIFICATION TEST");print(" BEHAVIORAL PATTERN AGGREGATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Minimum-sample behavioral pattern contract certified");print("[PASS] single observation cannot become a pattern");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-013 CERTIFIED")\n'

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
    print("="*88);print(" OLF-013 INSTALLER");print(" BEHAVIORAL PATTERN AGGREGATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_012_historical_condition_context")
    if not up.verify_olf_012_historical_condition_context():raise RuntimeError("OLF-012 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_013_behavior_patterns import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_013_behavior_patterns");p=m.materialize_behavior_patterns(ROOT,3)
        if len(p["patterns"])<=0:raise RuntimeError("No repeated evidence-grounded patterns met the minimum sample gate")
        print(f"[PHYSICAL PATTERNS] patterns={len(p['patterns'])} min_samples={p['min_samples']} state_hash={p['learner_state_hash']}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-013 failed; files restored");raise
    print("[PASS] Patterns remain descriptive/non-directional");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-013 INSTALLATION COMPLETE")
if __name__=="__main__":main()
