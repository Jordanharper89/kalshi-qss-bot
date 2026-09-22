from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_049_post_repair_settlement_cohort_read_model.py'
TEST=ROOT/'test_opc_049_post_repair_settlement_cohort_read_model.py'
SOURCE='from pathlib import Path\nfrom datetime import datetime\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch\nOPC_049_BUILD_ID="OPC-049"\ndef physical_probe(root=None,limit=100):\n root=Path(root or Path.cwd()).resolve();e=load_epoch(root);epoch=e["repair_epoch"]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:\n   cur.execute("SET TRANSACTION READ ONLY")\n   cur.execute("""SELECT ticker,settlement_ts,result,status,evidence_sequence_number FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s""",(epoch,int(limit)))\n   rows=cur.fetchall() or []\n  c.rollback()\n return {"repair_epoch":epoch,"post_repair_settlements":len(rows),"with_evidence_sequence":sum(r[4] is not None for r in rows),"statuses":{str(s):sum(str(r[3])==str(s) for r in rows) for s in sorted(set(r[3] for r in rows))},"sample":[tuple(map(lambda x: None if x is None else str(x),r)) for r in rows[:20]],"read_only":True,"probability_enabled":False,"execution_authority":False}\ndef verify_opc_049():return OPC_049_BUILD_ID=="OPC-049"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_049_post_repair_settlement_cohort_read_model as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_049());x=m.physical_probe();self.assertIn("post_repair_settlements",x);self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)\nif __name__=="__main__":unittest.main(verbosity=2)\n'

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
    print(' OPC-049 INSTALLER — POST-REPAIR SETTLEMENT COHORT READ MODEL')
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
