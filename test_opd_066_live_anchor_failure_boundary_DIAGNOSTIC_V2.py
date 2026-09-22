from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
root=Path.cwd()
runner=root/"run_oad_054_kalshi_global_fast_lane.py"
s=runner.read_text(encoding="utf-8")
print("[RUNNER_HOOK_IMPORT]", "opd_061_realtime_kalshi_anchor_tap import freeze_trade" in s)
print("[RUNNER_HOOK_CALL]", "freeze_trade(raw,now,observation.observation_id,root)" in s)
if "freeze_trade(raw,now,observation.observation_id,root)" in s:
 a=s.index("observation=build_ola_canonical_observation_from_websocket")
 b=s.index("freeze_trade(raw,now,observation.observation_id,root)")
 c=s.index("await _persist_without_transport_reconnect")
 print("[RUNNER_ORDER]",a<b<c)
spool=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
print("[SPOOL_EXISTS]",spool.exists(),"[BYTES]",spool.stat().st_size if spool.exists() else 0)
with connect(root,autocommit=False) as conn:
 with conn.cursor() as cur:
  cur.execute("SET TRANSACTION READ ONLY")
  cur.execute("SET LOCAL statement_timeout='5000ms'")
  cur.execute("""SELECT sequence_number,observation_type,canonical_observation_json
  FROM public.oracle_canonical_observations
  WHERE source_id='source.kalshi.market_data' AND observation_type='trade'
  ORDER BY sequence_number DESC LIMIT 5000""")
  rows=cur.fetchall() or []
 conn.rollback()
hits=[]
for seq,typ,obj in rows:
 p=obj.get("payload",{}) if isinstance(obj,dict) else {}
 m=p.get("message",{}) if isinstance(p,dict) else {}
 ticker=str(m.get("market_ticker") or "")
 if any(x in ticker.upper() for x in ("BTC","ETH","SOL")):
  hits.append((seq,ticker,m))
  if len(hits)>=5:break
print("[CRYPTO_TRADE_ROWS]",len(hits))
for seq,ticker,m in hits:
 print("[TRADE]",seq,ticker)
 print("[MESSAGE_KEYS]",sorted(m.keys()))
 print("[PRICE_VALUES]",{k:m.get(k) for k in ("yes_price_dollars","price_dollars","last_price_dollars","yes_price","price") if k in m})
assert "opd_061_realtime_kalshi_anchor_tap import freeze_trade" in s,"OPD064_IMPORT_MISSING_FROM_LIVE_RUNNER"
assert "freeze_trade(raw,now,observation.observation_id,root)" in s,"OPD064_CALL_MISSING_FROM_LIVE_RUNNER"
assert hits,"NO_RECENT_CRYPTO_TRADE_ROWS_FOR_SHAPE_DIAGNOSTIC"
print("[PASS] OPD-066 failure boundary physically isolated")
