def _db(root):
 import os
 from pathlib import Path
 url=os.environ.get("ORACLE_POSTGRESQL_URL") or os.environ.get("ORACLE_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
 if url:return url
 p=Path(root)/".env"
 if p.is_file():
  for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
   if "=" not in raw or raw.lstrip().startswith("#"):continue
   k,v=raw.split("=",1)
   if k.strip() in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL") and v.strip():return v.strip().strip('"').strip("'")
 raise RuntimeError("PostgreSQL URL not configured")
from pathlib import Path
OPC_047_BUILD_ID="OPC-047"
def physical_probe(root=None):
 root=Path(root or Path.cwd()).resolve();import psycopg;conn=psycopg.connect(_db(root))
 try:
  with conn.cursor() as cur:
   cur.execute("SELECT status,COUNT(*) FROM public.oracle_production_learning_ledger GROUP BY status");counts={str(k):int(v) for k,v in cur.fetchall()}
   cur.execute("SELECT COUNT(*) FROM public.oracle_production_learning_ledger WHERE evidence_sequence_number IS NOT NULL");linked=int(cur.fetchone()[0])
   cur.execute("SELECT COUNT(*) FROM public.oracle_production_learning_evidence_index WHERE sequence_number IS NOT NULL");indexed=int(cur.fetchone()[0])
 finally:conn.close()
 ready=linked>1 and counts.get("LEARNED",0)+counts.get("ELIGIBLE",0)>1
 return {"ledger_status_counts":counts,"ledger_with_evidence_sequence":linked,"evidence_index_with_sequence":indexed,"reconnection_ready":ready,"gate_status":"READY_FOR_EXISTING_OPL_OLR_RECONNECTION" if ready else "HOLD_FOR_NEW_POST_REPAIR_SETTLEMENT_EVIDENCE","probability_enabled":False,"read_only":True,"execution_authority":False}
def verify_opc_047():return OPC_047_BUILD_ID=="OPC-047"
