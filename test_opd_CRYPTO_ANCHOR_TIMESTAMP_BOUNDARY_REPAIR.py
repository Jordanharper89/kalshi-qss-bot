from datetime import datetime,timezone
import tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap as m
raw={"type":"trade","msg":{"market_ticker":"KXBTC15M-TEST","yes_price_dollars":"0.55"}}
with tempfile.TemporaryDirectory() as d:
 r=Path(d)
 a=m.freeze_trade(raw,1789161000.25,"float-anchor",r)
 b=m.freeze_trade(raw,datetime.fromtimestamp(1789161001.25,tz=timezone.utc),"datetime-anchor",r)
 assert a and b
 assert a["observed_epoch"]==1789161000.25
 assert b["observed_epoch"]==1789161001.25
 lines=(r/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl").read_text().splitlines()
 assert len(lines)==2
print("[PASS] OPD-061 accepts both production float epoch and datetime timestamp inputs")
print("[PASS] BTC live trade anchor no longer throws timestamp AttributeError")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
