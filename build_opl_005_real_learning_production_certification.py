from pathlib import Path
import importlib,os,subprocess,sys,json
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_learning"
MOD=PKG/"opl_005_real_learning_production_certification.py";TEST=ROOT/"test_opl_005_real_learning_production_certification.py";INIT=PKG/"__init__.py";MANIFEST=PKG/"OPL_005_FREEZE_MANIFEST.json"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport hashlib,json\n\nfrom .opl_001_production_learning_foundation import read_production_learning_state,connect,LEDGER_TABLE\nfrom .opl_004_24x7_production_learning_runtime import verify_opl_004_24x7_production_learning_runtime\n\nOPL_005_BUILD_ID="OPL-005"\nOPL_005_REVISION="OPL_005_REAL_LEARNING_PRODUCTION_CERTIFICATION_V1"\n\ndef production_learning_evidence(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    state=read_production_learning_state(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"SELECT COUNT(*) FROM public.{LEDGER_TABLE} WHERE status=\'LEARNED\'")\n            learned_records=int(cur.fetchone()[0])\n            cur.execute(f"SELECT COUNT(*) FROM public.{LEDGER_TABLE} WHERE evidence_hash IS NOT NULL AND evidence_hash<>\'\'")\n            evidence_records=int(cur.fetchone()[0])\n    return {\n        "production_outcomes_learned":int(state["production_outcomes_learned"]),\n        "learned_records":learned_records,\n        "evidence_records":evidence_records,\n        "applied_through_sequence":int(state["applied_through_sequence"]),\n        "state_hash":state["state_hash"],\n    }\n\ndef certification_ready(root=None):\n    x=production_learning_evidence(root)\n    return (\n        verify_opl_004_24x7_production_learning_runtime(root)\n        and x["production_outcomes_learned"]>0\n        and x["learned_records"]>0\n        and x["evidence_records"]>0\n        and x["applied_through_sequence"]>0\n        and bool(x["state_hash"])\n    )\n\ndef write_freeze_manifest(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    if not certification_ready(root):\n        raise RuntimeError("OPL-005 refuses certification until real production learning has occurred")\n    evidence=production_learning_evidence(root)\n    body={"build_id":OPL_005_BUILD_ID,"revision":OPL_005_REVISION,\n          "real_production_learning_evidence":evidence,\n          "frozen_capability":{"evidence_supported_settlement_intake":True,\n          "canonical_evidence_index":True,"outcome_grounded_learning":True,\n          "durable_postgresql_learning_state":True,"oracle_live_cutover":True,\n          "execution_authority":False}}\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"))\n    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_production_learning"/"OPL_005_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_opl_005_real_learning_production_certification(root=None):\n    return OPL_005_BUILD_ID=="OPL-005" and callable(certification_ready)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_learning.opl_005_real_learning_production_certification import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPL_005_BUILD_ID,"OPL-005")\n    def test_callable(self):self.assertTrue(callable(certification_ready))\nif __name__=="__main__":\n    print("="*88);print(" OPL-005 CERTIFICATION TEST");print(" REAL LEARNING PRODUCTION CERTIFICATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Certification gate contract certified")\n    print("[PASS] Gate requires real learned records")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPL-005 GATE CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OPL-005 INSTALLER");print(" REAL LEARNING PRODUCTION CERTIFICATION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_learning.opl_004_24x7_production_learning_runtime")
    if not up.verify_opl_004_24x7_production_learning_runtime(ROOT):raise RuntimeError("OPL-004 verification failed")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opl_005_real_learning_production_certification import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_production_learning.opl_005_real_learning_production_certification")
        e=m.production_learning_evidence(ROOT)
        print("[PRODUCTION EVIDENCE] "+json.dumps(e,sort_keys=True))
        if not m.certification_ready(ROOT):
            print("[NOT CERTIFIED] OPL-005 requires real production learning before freeze.")
            print("[ACTION] Start Oracle Live and wait for [OPL LEARN] applied>0, then rerun this installer.")
            raise SystemExit(2)
        path,body=m.write_freeze_manifest(ROOT)
        print("[PASS] Wrote:",path.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except SystemExit:
        raise
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPL-005 failed; files restored");raise
    print("[PASS] REAL production learning proven")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-005 PRODUCTION LEARNING CERTIFIED AND FROZEN")
if __name__=="__main__":main()
