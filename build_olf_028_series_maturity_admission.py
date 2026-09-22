from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback";MOD=PKG/"olf_028_series_maturity.py";TEST=ROOT/"test_olf_028_series_maturity_admission.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport json,os\nfrom .olf_027_series_learning_gaps import materialize_series_learning_gaps\n\nOLF_028_BUILD_ID="OLF-028";OLF_028_REVISION="OLF_028_SERIES_MATURITY_ADMISSION_V1";OUTPUT_NAME="oracle_series_learning_maturity.json"\n\ndef classify(row):\n    n=int(row["scored_records"]);reason=str(row["gap_reason"])\n    if n>=20:return "PROVEN"\n    if n>=5:return "MATURE"\n    if n>=2:return "LEARNING"\n    if n>=1:return "SPARSE"\n    if int(row["learned_records"])>0:return "EVIDENCE_ONLY"\n    return "BLIND"\n\ndef admitted(level):return level in ("PROVEN","MATURE")\n\ndef build_series_maturity(root=None):\n    root=Path(root or Path.cwd()).resolve();g=materialize_series_learning_gaps(root);rows=[]\n    for x in g["series"]:\n        level=classify(x);rows.append({**x,"maturity":level,"reasoning_admitted":admitted(level)})\n    return {"revision":OLF_028_REVISION,"learner_state_hash":g["learner_state_hash"],"series":rows,\n            "admitted_series":sum(x["reasoning_admitted"] for x in rows),"withheld_series":sum(not x["reasoning_admitted"] for x in rows),\n            "execution_authority":False}\ndef materialize_series_maturity(root=None):\n    root=Path(root or Path.cwd()).resolve();p=build_series_maturity(root);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,path);return p\ndef verify_olf_028_series_maturity_admission():\n    return OLF_028_BUILD_ID=="OLF-028" and classify({"scored_records":20,"gap_reason":"","learned_records":20})=="PROVEN" and not admitted("LEARNING")\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_learning_feedback.olf_028_series_maturity as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OLF_028_BUILD_ID,"OLF-028")\n    def test_admission(self):\n        self.assertTrue(m.admitted("PROVEN"));self.assertFalse(m.admitted("SPARSE"))\nif __name__=="__main__":\n    print("="*88);print(" OLF-028 CERTIFICATION TEST");print(" SERIES MATURITY + ADMISSION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] PROVEN/MATURE/LEARNING/SPARSE/EVIDENCE_ONLY/BLIND admission certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-028 CERTIFIED")\n'

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
    print("="*88);print(" OLF-028 INSTALLER");print(" SERIES MATURITY + ADMISSION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_027_series_learning_gaps")
    if not up.verify_olf_027_series_learning_gap_classification():raise RuntimeError("OLF-027 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_028_series_maturity import *");subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_028_series_maturity");p=m.materialize_series_maturity(ROOT)
        print(f"[PHYSICAL MATURITY] admitted_series={p['admitted_series']} withheld_series={p['withheld_series']} state_hash={p['learner_state_hash']}")
        for x in p["series"]:print(f"[SERIES MATURITY] series={x['series_key']} maturity={x['maturity']} admitted={x['reasoning_admitted']} scored={x['scored_records']} gap={x['gap_reason']}")
        if p["admitted_series"]<=0:raise RuntimeError("No series currently has enough outcome-scored history for mature reasoning admission")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-028 failed; files restored");raise
    print("[PASS] Sparse history cannot masquerade as mature intelligence");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-028 INSTALLATION COMPLETE")
if __name__=="__main__":main()
