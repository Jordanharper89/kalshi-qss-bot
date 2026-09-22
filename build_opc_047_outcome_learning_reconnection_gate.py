from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_047_outcome_learning_reconnection_gate.py'
TEST=ROOT/'test_opc_047_outcome_learning_reconnection_gate.py'
SOURCE='def _db(root):\n import os\n from pathlib import Path\n url=os.environ.get("ORACLE_POSTGRESQL_URL") or os.environ.get("ORACLE_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")\n if url:return url\n p=Path(root)/".env"\n if p.is_file():\n  for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n   if "=" not in raw or raw.lstrip().startswith("#"):continue\n   k,v=raw.split("=",1)\n   if k.strip() in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL") and v.strip():return v.strip().strip(\'"\').strip("\'")\n raise RuntimeError("PostgreSQL URL not configured")\nfrom pathlib import Path\nOPC_047_BUILD_ID="OPC-047"\ndef physical_probe(root=None):\n root=Path(root or Path.cwd()).resolve();import psycopg;conn=psycopg.connect(_db(root))\n try:\n  with conn.cursor() as cur:\n   cur.execute("SELECT status,COUNT(*) FROM public.oracle_production_learning_ledger GROUP BY status");counts={str(k):int(v) for k,v in cur.fetchall()}\n   cur.execute("SELECT COUNT(*) FROM public.oracle_production_learning_ledger WHERE evidence_sequence_number IS NOT NULL");linked=int(cur.fetchone()[0])\n   cur.execute("SELECT COUNT(*) FROM public.oracle_production_learning_evidence_index WHERE sequence_number IS NOT NULL");indexed=int(cur.fetchone()[0])\n finally:conn.close()\n ready=linked>1 and counts.get("LEARNED",0)+counts.get("ELIGIBLE",0)>1\n return {"ledger_status_counts":counts,"ledger_with_evidence_sequence":linked,"evidence_index_with_sequence":indexed,"reconnection_ready":ready,"gate_status":"READY_FOR_EXISTING_OPL_OLR_RECONNECTION" if ready else "HOLD_FOR_NEW_POST_REPAIR_SETTLEMENT_EVIDENCE","probability_enabled":False,"read_only":True,"execution_authority":False}\ndef verify_opc_047():return OPC_047_BUILD_ID=="OPC-047"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_047_outcome_learning_reconnection_gate as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_047());x=m.physical_probe();self.assertIn(x["gate_status"],("READY_FOR_EXISTING_OPL_OLR_RECONNECTION","HOLD_FOR_NEW_POST_REPAIR_SETTLEMENT_EVIDENCE"));self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def w(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)
def rr(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.write_bytes(b)
def main():
    print("="*88);print(' OPC-047 INSTALLER — OUTCOME / LEARNING RECONNECTION GATE');print("="*88);print("[ROOT]",ROOT)
    bm=TARGET.read_bytes() if TARGET.exists() else None
    bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified")
        w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
        modname=TARGET.with_suffix("").relative_to(ROOT).as_posix().replace("/",".")
        if modname in sys.modules: del sys.modules[modname]
        m=importlib.import_module(modname)
        if hasattr(m,"physical_probe"):
            print("[PHYSICAL]",m.physical_probe(ROOT))
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
    except Exception:
        rr(TARGET,bm);rr(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
    print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":
    main()
