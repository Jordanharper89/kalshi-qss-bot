from pathlib import Path

TEST = r'''from pathlib import Path
import json,inspect
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

root=Path.cwd();rt=root/"runtime"/"predictive_data"

def rows(p):
 return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []

anchors={x["anchor_id"]:x for x in rows(rt/"opd_061_live_anchor_spool.jsonl")}
done={x["state_id"] for x in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
states=[x for x in rows(rt/"opd_032_prospective_state_ledger.jsonl")
        if int(x.get("horizon_seconds",-1))==5 and x.get("anchor_id") in anchors and x["state_id"] not in done]

assert states,"NO_UNRESOLVED_LIVE_5S_STATES"

print("========== OPD-056 EXACT SOURCE ==========")
print(inspect.getsource(m))
print("==========================================")

samples=states[-20:]
physical=0
reachable=0

with connect(root,autocommit=False) as c:
 with c.cursor() as q:
  q.execute("SET TRANSACTION READ ONLY")
  q.execute("SET LOCAL statement_timeout='10000ms'")

  for s in samples:
   T=float(s["observed_epoch"]);ticker=s["ticker"]

   q.execute("""
   SELECT sequence_number,canonical_observation_json
   FROM public.oracle_canonical_observations
   WHERE source_id='source.kalshi.market_data'
     AND observation_type IN ('trade','ticker')
     AND canonical_observation_json->'payload'->'message'->>'market_ticker'=%s
   ORDER BY sequence_number DESC
   LIMIT 5000
   """,(ticker,))

   rr=q.fetchall() or []
   pts=[]

   for seq,obj in rr:
    p=obj.get("payload",{}) if isinstance(obj,dict) else {}
    msg=p.get("message",{}) if isinstance(p,dict) else {}
    try:
     et=float(msg["ts_ms"])/1000 if msg.get("ts_ms") is not None else float(msg["ts"])
    except Exception:
     continue

    v=msg.get("yes_price_dollars")
    if v is None:v=msg.get("price_dollars")

    try:v=float(v)
    except Exception:continue

    if T < et <= T+5:
     pts.append((int(seq),et,v))

   r=m.materialize_live(s,root)

   if pts:physical+=1
   if r is not None:reachable+=1

   print("[STATE]",s["state_id"][:12],ticker,
         "[POINTS]",len(pts),
         "[OPD056]",r is not None,
         "[T]",T)

 c.rollback()

print("[SAMPLED]",len(samples))
print("[PHYSICAL_5S_PATHS]",physical)
print("[OPD056_REACHABLE]",reachable)

if physical and reachable==0:
 print("[ROOT_CAUSE] OPD056_BOUNDED_READER_CANNOT_REACH_EXISTING_EXACT_TICKER_FUTURE_PATH")
elif physical and reachable:
 print("[ROOT_CAUSE] OPD056_CAN_REACH_AT_LEAST_SOME_PHYSICAL_5S_PATHS")
else:
 print("[ROOT_CAUSE] NO_EXACT_5S_FUTURE_PATH_IN_SAMPLED_LIVE_STATES")

print("[PASS] OPD-066 V5 exact-ticker outcome reachability diagnostic complete")
'''

Path("test_opd_066_exact_ticker_outcome_reachability_DIAGNOSTIC_V5.py").write_text(TEST,encoding="utf-8")
print("[PASS] OPD-066 diagnostic V5 installed")