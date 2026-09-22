from pathlib import Path
import json,time,inspect
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

root=Path.cwd();rt=root/"runtime"/"predictive_data"
sp=rt/"opd_061_live_anchor_spool.jsonl";st=rt/"opd_032_prospective_state_ledger.jsonl";ou=rt/"opd_033_prospective_outcome_ledger.jsonl"

def rows(p):
 return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []

anchors={x["anchor_id"]:x for x in rows(sp)}
resolved={x["state_id"] for x in rows(ou)}
five=[x for x in rows(st) if int(x.get("horizon_seconds",-1))==5 and x.get("anchor_id") in anchors and x["state_id"] not in resolved]
assert five,"NO_UNRESOLVED_LIVE_5S_STATE"
s=five[-1];a=anchors[s["anchor_id"]];T=float(s["observed_epoch"])

print("[STATE_ID]",s["state_id"])
print("[TICKER]",s["ticker"])
print("[T]",T,"[MATURITY]",T+5,"[AGE_NOW]",time.time()-T)
print("[ANCHOR_PRICE]",s.get("anchor_price"))
src=inspect.getsource(materialize_live)
print("[OPD056_HAS_AFTER_SEQUENCE]", "after_sequence" in src)
print("[OPD056_SOURCE_LINES]",len(src.splitlines()))

try:
 r=materialize_live(s,root)
 print("[OPD056_RESULT]",r)
except Exception as e:
 print("[OPD056_EXCEPTION]",type(e).__name__,str(e))

with connect(root,autocommit=False) as c:
 with c.cursor() as q:
  q.execute("SET TRANSACTION READ ONLY")
  q.execute("SET LOCAL statement_timeout='5000ms'")
  q.execute("""SELECT sequence_number,canonical_observation_json
  FROM public.oracle_canonical_observations
  WHERE source_id='source.kalshi.market_data'
  AND observation_type IN ('trade','ticker')
  ORDER BY sequence_number DESC LIMIT 50000""")
  rr=q.fetchall() or []
 c.rollback()

pts=[]
for seq,obj in rr:
 p=obj.get("payload",{}) if isinstance(obj,dict) else {}
 m=p.get("message",{}) if isinstance(p,dict) else {}
 if str(m.get("market_ticker") or "")!=s["ticker"]:continue
 try: et=float(m.get("ts_ms"))/1000 if m.get("ts_ms") is not None else float(m.get("ts"))
 except Exception:continue
 price=m.get("yes_price_dollars") or m.get("price_dollars")
 try: price=float(price)
 except Exception:continue
 if T < et <= T+5:pts.append((int(seq),et,price))

pts.sort(key=lambda x:(x[1],x[0]))
print("[PHYSICAL_FUTURE_POINTS_5S]",len(pts))
for x in pts[:10]:print("[POINT]",x)
print("[LATEST_DB_SEQUENCE]",rr[0][0] if rr else None)

if pts and r is None:
 print("[ROOT_CAUSE] PHYSICAL_FUTURE_PATH_EXISTS_BUT_OPD056_LIVE_READER_CANNOT_REACH_IT")
elif not pts:
 print("[ROOT_CAUSE] NO_PHYSICAL_FUTURE_POINT_IN_EXACT_5S_EVENT_WINDOW_FOR_THIS_STATE")
else:
 print("[ROOT_CAUSE] OPD056_CAN_MATERIALIZE_THIS_STATE")

print("[PASS] OPD-066 V4 live 5-second outcome boundary diagnostic complete")
