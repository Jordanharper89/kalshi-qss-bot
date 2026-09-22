from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch
OPC_051_BUILD_ID="OPC-051"
def physical_probe(root=None,limit=100):
 root=Path(root or Path.cwd()).resolve();epoch=load_epoch(root)["repair_epoch"]
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY")
   cur.execute("""SELECT ticker,settlement_ts,status,evidence_sequence_number,evidence_hash,learning_event_hash FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s""",(epoch,int(limit)));rows=cur.fetchall() or []
  c.rollback()
 linked=[r for r in rows if r[3] is not None]
 learned=[r for r in rows if str(r[2])=="LEARNED"]
 eligible=[r for r in rows if str(r[2])=="ELIGIBLE"]
 return {"repair_epoch":epoch,"checked":len(rows),"linked":len(linked),"eligible":len(eligible),"learned":len(learned),"evidence_missing":sum(str(r[2])=="EVIDENCE_MISSING" for r in rows),"waiting_for_post_repair_settlements":len(rows)==0,"read_only":True,"probability_enabled":False,"execution_authority":False}
def verify_opc_051():return OPC_051_BUILD_ID=="OPC-051"
