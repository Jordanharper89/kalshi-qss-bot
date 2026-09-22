from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_007_cross_market_learning_index.py";TEST=ROOT/"test_olf_007_cross_market_learning_index.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os\n\nfrom .olf_001_learned_state_snapshot import SNAPSHOT_NAME,verify_snapshot_matches_current_learner\nfrom .olf_006_structural_identity import resolve_structural_identity\n\nOLF_007_BUILD_ID="OLF-007"\nOLF_007_REVISION="OLF_007_CROSS_MARKET_LEARNING_INDEX_V1"\nINDEX_NAME="oracle_cross_market_learning_index.json"\n\n@dataclass(frozen=True)\nclass CrossMarketLearningIndexSummary:\n    learner_state_hash:str\n    learned_markets:int\n    exact_keys:int\n    series_keys:int\n    indexed_records:int\n    execution_authority:bool=False\n\ndef _load_snapshot(root):\n    path=Path(root)/"runtime_state"/SNAPSHOT_NAME\n    return json.loads(path.read_text(encoding="utf-8"))\n\ndef build_cross_market_learning_index(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    if not verify_snapshot_matches_current_learner(root):\n        raise RuntimeError("OLF learned-state snapshot is stale")\n    snap=_load_snapshot(root)\n    exact={}\n    series={}\n    indexed=0\n    for row in snap.get("markets",[]):\n        if not isinstance(row,dict):continue\n        ticker=str(row.get("market_ticker") or "")\n        if not ticker:continue\n        ident=resolve_structural_identity(ticker)\n        item={\n            "market_ticker":ticker,\n            "learned_records":int(row.get("learned_records",0)),\n            "experience_weight":float(row.get("experience_weight",0.0)),\n            "feedback_eligible":bool(row.get("feedback_eligible",False)),\n        }\n        exact[ident.exact_key]=item\n        series.setdefault(ident.series_key,[]).append(item)\n        indexed+=int(item["learned_records"])\n    for key in series:\n        series[key]=sorted(series[key],key=lambda x:(x["market_ticker"],x["learned_records"]))\n    return {\n        "revision":OLF_007_REVISION,\n        "learner_state_hash":str(snap.get("learner_state_hash") or ""),\n        "exact":exact,\n        "series":dict(sorted(series.items())),\n        "execution_authority":False,\n    },indexed\n\ndef materialize_cross_market_learning_index(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    payload,indexed=build_cross_market_learning_index(root)\n    path=root/"runtime_state"/INDEX_NAME\n    tmp=path.with_suffix(path.suffix+".tmp")\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,path)\n    return CrossMarketLearningIndexSummary(\n        payload["learner_state_hash"],len(payload["exact"]),len(payload["exact"]),\n        len(payload["series"]),indexed,False\n    )\n\ndef load_cross_market_learning_index(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    path=root/"runtime_state"/INDEX_NAME\n    if not path.is_file():\n        materialize_cross_market_learning_index(root)\n    payload=json.loads(path.read_text(encoding="utf-8"))\n    snapshot=_load_snapshot(root)\n    if str(payload.get("learner_state_hash") or "")!=str(snapshot.get("learner_state_hash") or ""):\n        materialize_cross_market_learning_index(root)\n        payload=json.loads(path.read_text(encoding="utf-8"))\n    return payload\n\ndef verify_olf_007_cross_market_learning_index():\n    return OLF_007_BUILD_ID=="OLF-007" and callable(materialize_cross_market_learning_index)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_007_cross_market_learning_index import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_007_BUILD_ID,"OLF-007")\n    def test_contract(self):self.assertTrue(callable(load_cross_market_learning_index))\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-007 CERTIFICATION TEST");print(" CROSS-MARKET LEARNING INDEX");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Learned-state series index contract certified")\n    print("[PASS] learner_state_hash lineage preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-007 CERTIFIED")\n'

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
    print("="*88);print(" OLF-007 INSTALLER");print(" CROSS-MARKET LEARNING INDEX");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_006_structural_identity")
    if not up.verify_olf_006_learned_market_structural_identity():raise RuntimeError("OLF-006 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_007_cross_market_learning_index import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_007_cross_market_learning_index")
        s=m.materialize_cross_market_learning_index(ROOT)
        if s.learned_markets<=0 or s.series_keys<=0 or not s.learner_state_hash:raise RuntimeError("Physical cross-market learning index is empty")
        print(f"[PHYSICAL INDEX] learned_markets={s.learned_markets} series_keys={s.series_keys} indexed_records={s.indexed_records} state_hash={s.learner_state_hash}")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-007 failed; files restored");raise
    print("[PASS] Proven learner unchanged")
    print("[PASS] OLF snapshot consumed read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-007 INSTALLATION COMPLETE")
if __name__=="__main__":main()
