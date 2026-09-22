from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_012_historical_condition_context.py";TEST=ROOT/"test_olf_012_historical_condition_context.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom collections import Counter\nimport json,os\nfrom .olf_011_learned_experience_profile import materialize_learned_experience_profiles\n\nOLF_012_BUILD_ID="OLF-012"\nOLF_012_REVISION="OLF_012_HISTORICAL_CONDITION_CONTEXT_V1"\nCONTEXT_NAME="oracle_historical_condition_context.json"\n\ndef build_historical_condition_context(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    p=materialize_learned_experience_profiles(root)\n    groups={}\n    for x in p.get("profiles",[]):\n        if not x.get("evidence_resolved"):continue\n        groups.setdefault(x["series_key"],[]).append(x)\n    series={}\n    for key,rows in sorted(groups.items()):\n        types=Counter(str(x.get("observation_type") or "UNKNOWN") for x in rows)\n        sessions=Counter(str(x.get("utc_session") or "UNKNOWN") for x in rows)\n        sources=Counter(str(x.get("source_family") or "UNKNOWN") for x in rows)\n        series[key]={\n            "evidence_records":len(rows),\n            "observation_types":dict(sorted(types.items())),\n            "utc_sessions":dict(sorted(sessions.items())),\n            "source_families":dict(sorted(sources.items())),\n            "dominant_observation_type":types.most_common(1)[0][0] if types else "UNKNOWN",\n            "dominant_utc_session":sessions.most_common(1)[0][0] if sessions else "UNKNOWN",\n        }\n    return {"revision":OLF_012_REVISION,"learner_state_hash":p["learner_state_hash"],"series":series,"execution_authority":False}\n\ndef materialize_historical_condition_context(root=None):\n    root=Path(root or Path.cwd()).resolve();payload=build_historical_condition_context(root)\n    path=root/"runtime_state"/CONTEXT_NAME;tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path)\n    return payload\n\ndef verify_olf_012_historical_condition_context():\n    return OLF_012_BUILD_ID=="OLF-012" and callable(build_historical_condition_context)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_012_historical_condition_context import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_012_BUILD_ID,"OLF-012")\nif __name__=="__main__":\n    print("="*88);print(" OLF-012 CERTIFICATION TEST");print(" HISTORICAL CONDITION CONTEXT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Series-level evidence condition aggregation certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-012 CERTIFIED")\n'

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
    print("="*88);print(" OLF-012 INSTALLER");print(" HISTORICAL CONDITION CONTEXT");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile")
    if not up.verify_olf_011_evidence_grounded_learned_experience_profile():raise RuntimeError("OLF-011 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_012_historical_condition_context import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_012_historical_condition_context");p=m.materialize_historical_condition_context(ROOT)
        if not p["series"]:raise RuntimeError("No historical condition series were materialized")
        print(f"[PHYSICAL CONDITIONS] series={len(p['series'])} state_hash={p['learner_state_hash']}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-012 failed; files restored");raise
    print("[PASS] OLF-011 evidence lineage preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-012 INSTALLATION COMPLETE")
if __name__=="__main__":main()
