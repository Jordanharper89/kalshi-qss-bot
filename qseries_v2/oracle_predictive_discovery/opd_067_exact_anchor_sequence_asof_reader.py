from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import exact_anchor_sequence
execution_authority=False
CB="source.crypto.hf.coinbase.historical_window"
COND="source.crypto.condition."
LEARN="source.crypto.learned_case."

def read_before_anchor(anchor,root=None,limit=50000):
 root=Path(root or Path.cwd())
 seq=exact_anchor_sequence(anchor,root)
 if seq is None:return [],None
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY")
   q.execute("SET LOCAL statement_timeout='5000ms'")
   q.execute("""WITH recent AS MATERIALIZED (
    SELECT sequence_number,source_id,observation_type,canonical_observation_json
    FROM public.oracle_canonical_observations
    WHERE sequence_number<=%s
    ORDER BY sequence_number DESC LIMIT %s)
   SELECT sequence_number,source_id,observation_type,canonical_observation_json
   FROM recent
   WHERE source_id=%s OR source_id LIKE %s OR source_id LIKE %s
   ORDER BY sequence_number DESC""",
   (int(seq),int(limit),CB,COND+"%",LEARN+"%"))
   rows=q.fetchall() or []
  c.rollback()
 return rows,int(seq)
