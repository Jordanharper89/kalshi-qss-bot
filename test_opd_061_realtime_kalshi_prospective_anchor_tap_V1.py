from pathlib import Path
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
