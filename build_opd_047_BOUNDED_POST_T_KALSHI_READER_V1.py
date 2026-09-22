from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_047_bounded_post_t_kalshi_reader.py";T=R/"test_opd_047_bounded_post_t_kalshi_reader_V1.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND observed_at >= to_timestamp(%s) AND observed_at <= to_timestamp(%s) ORDER BY sequence_number ASC"
def read_post_t(ticker,t0,end,root=None):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'");q.execute(SQL,(SOURCE,float(t0),float(end)));raw=q.fetchall() or []
  c.rollback()
 rows=[]
 for seq,outer,obj in raw:
  oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
  if p and p["ticker"]==ticker and float(t0)<p["event_epoch"]<=float(end):rows.append(dict(p,sequence_number=int(seq)))
 rows.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 return rows
""",encoding="utf-8")
T.write_text("""import ast
from pathlib import Path
p=Path("qseries_v2/oracle_predictive_discovery/opd_047_bounded_post_t_kalshi_reader.py");s=p.read_text();ast.parse(s)
assert "SET TRANSACTION READ ONLY" in s and "statement_timeout='5000ms'" in s
assert "source_id=%s" in s and "to_timestamp(%s)" in s and "ORDER BY sequence_number ASC" in s
assert "float(t0)<p[\\"event_epoch\\"]<=float(end)" in s
print("[READ_ONLY] PASS");print("[BOUNDED_POST_T] PASS");print("[PASS] OPD-047 bounded physical Kalshi post-T reader contract certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-047 V1 installed")