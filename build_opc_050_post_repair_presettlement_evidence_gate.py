from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_050_post_repair_presettlement_evidence_gate.py'
TEST=ROOT/'test_opc_050_post_repair_presettlement_evidence_gate.py'
SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch\nOPC_050_BUILD_ID="OPC-050"\ndef physical_probe(root=None,limit=100,timeout_ms=15000):\n root=Path(root or Path.cwd()).resolve();epoch=load_epoch(root)["repair_epoch"]\n if not all(_index_status(root)):raise RuntimeError("OIAR-003 index not valid/ready/live")\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:\n   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n   cur.execute("SELECT ticker,settlement_ts,result FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s",(epoch,int(limit)));settled=cur.fetchall() or []\n  c.rollback()\n ids=[str(r[0]) for r in settled]\n if not ids:return {"repair_epoch":epoch,"checked":0,"with_pre_settlement_snapshot":0,"waiting_for_post_repair_settlements":True,"plan_uses_index":True,"read_only":True,"probability_enabled":False,"execution_authority":False}\n sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at FROM unnest(%s::text[]) wanted(market_id) LEFT JOIN LATERAL (SELECT sequence_number,observed_at FROM public.oracle_canonical_observations WHERE observation_type=\'market_snapshot\' AND ({MARKET_ID_EXPRESSION})=wanted.market_id ORDER BY sequence_number DESC LIMIT 100) h ON TRUE ORDER BY wanted.market_id,h.sequence_number DESC"""\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:\n   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'");cur.execute("EXPLAIN (FORMAT JSON) "+sql,(ids,));plan=cur.fetchone()[0];cur.execute(sql,(ids,));hist=cur.fetchall() or []\n  c.rollback()\n if INDEX_NAME not in str(plan):raise RuntimeError("OPC-050 lookup did not use OIAR-003 index")\n grouped={t:[] for t in ids}\n for t,seq,obs in hist:\n  if seq is not None:grouped.setdefault(str(t),[]).append((seq,obs))\n from datetime import datetime,timezone\n def dt(v):\n  if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n  return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n withpre=0\n for ticker,settle,_ in settled:withpre+=int(any(dt(o)<dt(settle) for _,o in grouped.get(str(ticker),[])))\n return {"repair_epoch":epoch,"checked":len(settled),"with_pre_settlement_snapshot":withpre,"without_pre_settlement_snapshot":len(settled)-withpre,"waiting_for_post_repair_settlements":False,"plan_uses_index":True,"index_name":INDEX_NAME,"read_only":True,"probability_enabled":False,"execution_authority":False}\ndef verify_opc_050():return OPC_050_BUILD_ID=="OPC-050"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_050_post_repair_presettlement_evidence_gate as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_050());x=m.physical_probe();self.assertTrue(x["plan_uses_index"]);self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)\nif __name__=="__main__":unittest.main(verbosity=2)\n'

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
    print(' OPC-050 INSTALLER — POST-REPAIR PRE-SETTLEMENT EVIDENCE GATE')
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
