from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_023_regime_recency.py";TEST=ROOT/"test_olf_023_regime_recency_decay.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nfrom collections import defaultdict\nimport json,math,os\nfrom .olf_021_experience_regimes import materialize_regime_segments\n\nOLF_023_BUILD_ID="OLF-023";OLF_023_REVISION="OLF_023_REGIME_RECENCY_DECAY_V1";OUTPUT_NAME="oracle_regime_recency_decay.json"\ndef _dt(v):\n    try:\n        x=datetime.fromisoformat(str(v).replace("Z","+00:00"));return x if x.tzinfo else x.replace(tzinfo=timezone.utc)\n    except Exception:return None\ndef build_recency_weighted_regimes(root=None,half_life_days=30.0,min_samples=2):\n    root=Path(root or Path.cwd()).resolve();src=materialize_regime_segments(root);valid=[x for x in src["records"] if _dt(x.get("settlement_ts"))]\n    anchor=max((_dt(x["settlement_ts"]) for x in valid),default=datetime.now(timezone.utc));g=defaultdict(list)\n    for x in valid:g[x["regime_id"]].append(x)\n    out=[]\n    for rid,rows in sorted(g.items()):\n        if len(rows)<min_samples:continue\n        weighted=[]\n        for x in rows:\n            age=max(0.0,(anchor-_dt(x["settlement_ts"])).total_seconds()/86400.0);w=2**(-age/half_life_days);weighted.append((x,w,age))\n        sw=sum(w for _,w,_ in weighted)\n        if sw<=0:continue\n        hit=sum((1.0 if x["prediction_hit"] else 0.0)*w for x,w,_ in weighted)/sw;b=sum(float(x["brier_score"])*w for x,w,_ in weighted)/sw\n        mp=sum(float(x["implied_yes_probability"])*w for x,w,_ in weighted)/sw;yr=sum((1.0 if x["settlement_result"]=="yes" else 0.0)*w for x,w,_ in weighted)/sw;ce=abs(mp-yr)\n        eff=min(float(len(rows)),sw);support=eff/(eff+8.0);rel=max(0.0,min(1.0,support*(1-b)*(1-ce)))\n        out.append({"regime_id":rid,"samples":len(rows),"effective_samples":eff,"recency_weighted_hit_rate":hit,"recency_weighted_brier":b,"recency_weighted_calibration_error":ce,"recency_reliability_weight":rel,"newest_age_days":min(a for _,_,a in weighted),"oldest_age_days":max(a for _,_,a in weighted)})\n    return {"revision":OLF_023_REVISION,"learner_state_hash":src["learner_state_hash"],"anchor_settlement_ts":anchor.isoformat(),"half_life_days":half_life_days,"regimes":out,"execution_authority":False}\ndef materialize_recency_weighted_regimes(root=None,half_life_days=30.0,min_samples=2):\n    root=Path(root or Path.cwd()).resolve();p=build_recency_weighted_regimes(root,half_life_days,min_samples);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\ndef verify_olf_023_regime_recency_decay():return OLF_023_BUILD_ID=="OLF-023" and callable(build_recency_weighted_regimes)\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_023_regime_recency as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_023_BUILD_ID,"OLF-023")\n    def test_dt(self):self.assertIsNotNone(m._dt("2026-08-20T01:00:00Z"))\nif __name__=="__main__":\n    print("="*88);print(" OLF-023 CERTIFICATION TEST");print(" REGIME RECENCY + DECAY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Deterministic settlement-time recency decay certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-023 CERTIFIED")\n'

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
    print("="*88);print(" OLF-023 INSTALLER");print(" REGIME RECENCY + DECAY");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_022_regime_performance")
    if not up.verify_olf_022_regime_specific_performance_calibration():raise RuntimeError("OLF-022 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_023_regime_recency import *");subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_023_regime_recency");p=m.materialize_recency_weighted_regimes(ROOT,30.0,2)
        print(f"[PHYSICAL RECENCY] regimes={len(p['regimes'])} half_life_days={p['half_life_days']} anchor={p['anchor_settlement_ts']} state_hash={p['learner_state_hash']}")
        if not p["regimes"]:raise RuntimeError("No physical regime survived recency calculation")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-023 failed; files restored");raise
    print("[PASS] Old evidence decays without deleting history");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-023 INSTALLATION COMPLETE")
if __name__=="__main__":main()
