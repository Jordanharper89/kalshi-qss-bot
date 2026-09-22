from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_051_post_repair_learning_linkage_gate.py'
TEST=ROOT/'test_opc_051_post_repair_learning_linkage_gate.py'
SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch\nOPC_051_BUILD_ID="OPC-051"\ndef physical_probe(root=None,limit=100):\n root=Path(root or Path.cwd()).resolve();epoch=load_epoch(root)["repair_epoch"]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:\n   cur.execute("SET TRANSACTION READ ONLY")\n   cur.execute("""SELECT ticker,settlement_ts,status,evidence_sequence_number,evidence_hash,learning_event_hash FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s""",(epoch,int(limit)));rows=cur.fetchall() or []\n  c.rollback()\n linked=[r for r in rows if r[3] is not None]\n learned=[r for r in rows if str(r[2])=="LEARNED"]\n eligible=[r for r in rows if str(r[2])=="ELIGIBLE"]\n return {"repair_epoch":epoch,"checked":len(rows),"linked":len(linked),"eligible":len(eligible),"learned":len(learned),"evidence_missing":sum(str(r[2])=="EVIDENCE_MISSING" for r in rows),"waiting_for_post_repair_settlements":len(rows)==0,"read_only":True,"probability_enabled":False,"execution_authority":False}\ndef verify_opc_051():return OPC_051_BUILD_ID=="OPC-051"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_051_post_repair_learning_linkage_gate as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_051());x=m.physical_probe();self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)\nif __name__=="__main__":unittest.main(verbosity=2)\n'

def atomic_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,before):
    if before is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(before)

def main():
    print("="*88)
    print(' OPC-051 INSTALLER — POST-REPAIR LEARNING LINKAGE GATE')
    print("="*88)
    print("[ROOT]",ROOT)
    before_m=TARGET.read_bytes() if TARGET.exists() else None
    before_t=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE); ast.parse(TEST_SOURCE)
        print("[PASS] payload syntax verified")
        atomic_write(TARGET,SOURCE); atomic_write(TEST,TEST_SOURCE)
        importlib.invalidate_caches()
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
    except Exception:
        restore(TARGET,before_m); restore(TEST,before_t)
        print("[ROLLBACK] installation failed; affected files restored")
        raise
    print("[DONE] INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
