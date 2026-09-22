from pathlib import Path

M=r'''from pathlib import Path
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
   q.execute("""SELECT sequence_number,source_id,observation_type,canonical_observation_json
   FROM public.oracle_canonical_observations
   WHERE sequence_number<=%s
   ORDER BY sequence_number DESC LIMIT %s""",(int(seq),int(limit)))
   rows=q.fetchall() or []
  c.rollback()
 keep=[x for x in rows if x[1]==CB or str(x[1]).startswith(COND) or str(x[1]).startswith(LEARN)]
 return keep,int(seq)
'''

T=r'''from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_067_exact_anchor_sequence_asof_reader import read_before_anchor,CB,COND,LEARN
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
a=json.loads([x for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()][-1])
t=time.time();rows,seq=read_before_anchor(a,root);dt=time.time()-t
assert seq is not None and rows
counts={"coinbase":0,"condition":0,"learned":0}
for _,s,_,_ in rows:
 if s==CB:counts["coinbase"]+=1
 elif str(s).startswith(COND):counts["condition"]+=1
 elif str(s).startswith(LEARN):counts["learned"]+=1
print("[ANCHOR_ID]",a["anchor_id"])
print("[ANCHOR_SEQUENCE]",seq)
print("[ROWS]",len(rows),"[COUNTS]",counts,"[SECONDS]",round(dt,3))
assert counts["coinbase"]>0 and counts["condition"]>0 and counts["learned"]>0
assert dt<5.0
print("[EXECUTION_AUTHORITY] FALSE")
print("[PASS] OPD-067 exact-anchor sequence-bounded strict as-of read pavement certified")
'''

r=Path.cwd()
m=r/"qseries_v2/oracle_predictive_discovery/opd_067_exact_anchor_sequence_asof_reader.py"
m.write_text(M,encoding="utf-8")
(r/"test_opd_067_exact_anchor_sequence_asof_reader.py").write_text(T,encoding="utf-8")
import py_compile
py_compile.compile(str(m),doraise=True)
py_compile.compile(str(r/"test_opd_067_exact_anchor_sequence_asof_reader.py"),doraise=True)
print("[PASS] OPD-067 installed")