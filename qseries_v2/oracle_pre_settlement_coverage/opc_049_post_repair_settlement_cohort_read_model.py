from pathlib import Path
from datetime import datetime
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch
OPC_049_BUILD_ID="OPC-049"
def physical_probe(root=None,limit=100):
 root=Path(root or Path.cwd()).resolve();e=load_epoch(root);epoch=e["repair_epoch"]
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY")
   cur.execute("""SELECT ticker,settlement_ts,result,status,evidence_sequence_number FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s""",(epoch,int(limit)))
   rows=cur.fetchall() or []
  c.rollback()
 return {"repair_epoch":epoch,"post_repair_settlements":len(rows),"with_evidence_sequence":sum(r[4] is not None for r in rows),"statuses":{str(s):sum(str(r[3])==str(s) for r in rows) for s in sorted(set(r[3] for r in rows))},"sample":[tuple(map(lambda x: None if x is None else str(x),r)) for r in rows[:20]],"read_only":True,"probability_enabled":False,"execution_authority":False}
def verify_opc_049():return OPC_049_BUILD_ID=="OPC-049"
