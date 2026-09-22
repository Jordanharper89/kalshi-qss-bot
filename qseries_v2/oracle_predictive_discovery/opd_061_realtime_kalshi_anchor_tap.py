from pathlib import Path
import json,os
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _asset(ticker):
    u=str(ticker or "").upper().strip()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return None


def _canonical_highwater(root):
    with connect(Path(root),autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='5000ms'")
            q.execute("SELECT sequence_number FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 1")
            row=q.fetchone()
        c.rollback()
    return int(row[0]) if row else 0

def freeze_trade(raw,received_at,observation_id,root=None):
    if not isinstance(raw,dict): return None
    typ=str(raw.get("type") or "").strip().lower()
    if typ not in ("trade","ticker"): return None
    msg=raw.get("msg") or {}
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()
    asset=_asset(ticker)
    if not asset: return None
    price=None
    for k in ("yes_price_dollars","price_dollars","last_price_dollars"):
        try:
            v=float(msg[k])
            if 0.0<=v<=1.0: price=v; break
        except Exception: pass
    if price is None:
        try:
            b=float(msg.get("yes_bid_dollars")); a=float(msg.get("yes_ask_dollars"))
            if 0.0<=b<=1.0 and 0.0<=a<=1.0 and b<=a: price=(b+a)/2.0
        except Exception: pass
    if price is None: return None
    root=Path(root or Path.cwd())
    t=float(received_at.timestamp()) if hasattr(received_at,"timestamp") else float(received_at)
    boundary=_canonical_highwater(root)
    row={"schema_version":"OPD-061","anchor_id":str(observation_id),"ticker":ticker,
         "asset":asset,"observed_epoch":t,"anchor_price":price,
         "anchor_sequence_boundary":boundary,
         "anchor_sequence_basis":"CANONICAL_HIGHWATER_AT_FREEZE",
         "kalshi_state":{"sequence_number":boundary,"event_epoch":t,"trade_price":price,
         "yes_bid":msg.get("yes_bid_dollars"),"yes_ask":msg.get("yes_ask_dollars"),
         "spread":None,"yes_bid_size":msg.get("yes_bid_size"),"yes_ask_size":msg.get("yes_ask_size"),
         "last_trade_size":msg.get("count_fp"),"volume":msg.get("volume_fp") or msg.get("volume"),
         "open_interest":msg.get("open_interest_fp") or msg.get("open_interest"),
         "observation_type":typ,"event_time_path":"LIVE_RECEIVED_AT"},"post_freeze":True}
    p=root/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl"
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n"); f.flush(); os.fsync(f.fileno())
    return row

