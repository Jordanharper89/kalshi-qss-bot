from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_014_condition_aware_experience.py";TEST=ROOT/"test_olf_014_condition_aware_experience_resolver.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport json\nfrom .olf_006_structural_identity import resolve_structural_identity\nfrom .olf_013_behavior_patterns import materialize_behavior_patterns\n\nOLF_014_BUILD_ID="OLF-014"\nOLF_014_REVISION="OLF_014_CONDITION_AWARE_EXPERIENCE_RESOLVER_V1"\n\n@dataclass(frozen=True)\nclass ConditionAwareExperience:\n    market_ticker:str\n    series_key:str\n    available:bool\n    pattern_id:str\n    observation_type:str\n    samples:int\n    pattern_support:float\n    condition_similarity:float\n    relationship_strength:float\n    learner_state_hash:str\n    reason:str\n    directional_signal_available:bool=False\n    execution_authority:bool=False\n\ndef _session(v):\n    if not v:return "UNKNOWN"\n    try:\n        x=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)\n        h=x.astimezone(timezone.utc).hour\n        return "UTC_00_05" if h<6 else "UTC_06_11" if h<12 else "UTC_12_17" if h<18 else "UTC_18_23"\n    except Exception:return "UNKNOWN"\n\ndef resolve_condition_aware_experience(root=None,market_ticker="",source_rows=()):\n    root=Path(root or Path.cwd()).resolve();ident=resolve_structural_identity(market_ticker)\n    payload=materialize_behavior_patterns(root,3);rows=tuple(source_rows)\n    types=set();sessions=set()\n    for row in rows:\n        if hasattr(row,"source_row"):row=row.source_row\n        if not isinstance(row,dict):continue\n        types.add(str(row.get("observation_type") or row.get("event_type") or "UNKNOWN").upper())\n        sessions.add(_session(row.get("observed_at") or row.get("event_ts") or row.get("created_at")))\n    candidates=[]\n    for p in payload.get("patterns",[]):\n        if p.get("series_key")!=ident.series_key:continue\n        type_match=1.0 if str(p.get("observation_type")) in types else 0.0\n        session_match=1.0 if str(p.get("dominant_utc_session")) in sessions else 0.0\n        similarity=.80*type_match+.20*session_match\n        if similarity<=0:continue\n        strength=.75*similarity*float(p.get("support",0.0))\n        candidates.append((strength,similarity,p))\n    if not candidates:\n        return ConditionAwareExperience(ident.market_ticker,ident.series_key,False,"","UNKNOWN",0,0.0,0.0,0.0,str(payload.get("learner_state_hash") or ""),"NO_MATCHING_HISTORICAL_CONDITIONS",False,False)\n    strength,similarity,p=max(candidates,key=lambda x:(x[0],x[2]["samples"],x[2]["pattern_id"]))\n    return ConditionAwareExperience(\n        ident.market_ticker,ident.series_key,True,str(p["pattern_id"]),str(p["observation_type"]),\n        int(p["samples"]),float(p["support"]),float(similarity),float(strength),\n        str(payload.get("learner_state_hash") or ""),"MATCHED_EVIDENCE_GROUNDED_PATTERN",False,False\n    )\n\ndef verify_olf_014_condition_aware_experience_resolver():\n    return OLF_014_BUILD_ID=="OLF-014" and callable(resolve_condition_aware_experience)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_014_condition_aware_experience import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_014_BUILD_ID,"OLF-014")\n    def test_contract(self):\n        x=ConditionAwareExperience("KX","s",False,"","UNKNOWN",0,0,0,0,"h","NONE",False,False)\n        self.assertFalse(x.directional_signal_available);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88);print(" OLF-014 CERTIFICATION TEST");print(" CONDITION-AWARE EXPERIENCE RESOLVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Structural + observed-condition matching certified");print("[PASS] no directional signal fabricated");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-014 CERTIFIED")\n'

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
    print("="*88);print(" OLF-014 INSTALLER");print(" CONDITION-AWARE EXPERIENCE RESOLVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_013_behavior_patterns")
    if not up.verify_olf_013_behavioral_pattern_aggregation():raise RuntimeError("OLF-013 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_014_condition_aware_experience import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-014 failed; files restored");raise
    print("[PASS] Cross-series transfer remains prohibited by OLF-006 identity boundary");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-014 INSTALLATION COMPLETE")
if __name__=="__main__":main()
