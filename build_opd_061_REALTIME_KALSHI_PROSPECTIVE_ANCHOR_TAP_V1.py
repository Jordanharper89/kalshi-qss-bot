from pathlib import Path
MODULE=r'''from pathlib import Path
import json,os
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _asset(ticker):
    u=str(ticker).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
    return None

def freeze_trade(raw,received_at,observation_id,root=None):
    if not isinstance(raw,dict) or str(raw.get("type",""))!="trade":return None
    msg=raw.get("msg") or {}
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()
    asset=_asset(ticker)
    if not asset:return None
    price=None
    for k in ("yes_price_dollars","price_dollars","last_price_dollars"):
        try:
            v=float(msg[k])
            if 0.0<=v<=1.0:price=v;break
        except Exception:pass
    if price is None:return None
    t=float(received_at.timestamp())
    row={"schema_version":"OPD-061","anchor_id":str(observation_id),"ticker":ticker,
         "asset":asset,"observed_epoch":t,"anchor_price":price,
         "kalshi_state":{"sequence_number":None,"event_epoch":t,"trade_price":price,
         "yes_bid":msg.get("yes_bid_dollars"),"yes_ask":msg.get("yes_ask_dollars"),
         "spread":None,"yes_bid_size":msg.get("yes_bid_size"),"yes_ask_size":msg.get("yes_ask_size"),
         "last_trade_size":msg.get("count_fp"),"volume":None,"open_interest":None,
         "observation_type":"trade","event_time_path":"LIVE_RECEIVED_AT"},"post_freeze":True}
    root=Path(root or Path.cwd());p=root/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl"
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n");f.flush();os.fsync(f.fileno())
    return row
'''
TEST=r'''from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timezone
import json
from qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap import freeze_trade
with TemporaryDirectory() as td:
 r=freeze_trade({"type":"trade","msg":{"market_ticker":"KXBTC15M-X","yes_price_dollars":"0.61","count_fp":3}},datetime.fromtimestamp(1000,tz=timezone.utc),"obs-1",td)
 assert r["observed_epoch"]==1000 and r["anchor_price"]==0.61 and r["asset"]=="BTC"
 assert r["kalshi_state"]["event_time_path"]=="LIVE_RECEIVED_AT"
 assert freeze_trade({"type":"ticker","msg":{"market_ticker":"KXBTC-X"}},datetime.now(timezone.utc),"x",td) is None
 rows=[json.loads(x) for x in (Path(td)/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl").read_text().splitlines()]
 assert len(rows)==1 and rows[0]["anchor_id"]=="obs-1"
 print("[PASS] OPD-061 real-time pre-persistence prospective anchor tap certified")
'''
root=Path.cwd();m=root/"qseries_v2/oracle_predictive_discovery/opd_061_realtime_kalshi_anchor_tap.py"
m.parent.mkdir(parents=True,exist_ok=True);m.write_text(MODULE,encoding="utf-8")
(root/"test_opd_061_realtime_kalshi_prospective_anchor_tap_V1.py").write_text(TEST,encoding="utf-8")
print("[PASS] OPD-061 V1 installed")
