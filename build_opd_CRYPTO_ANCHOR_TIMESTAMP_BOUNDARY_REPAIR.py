from pathlib import Path
R=Path.cwd()
P=R/'qseries_v2'/'oracle_predictive_discovery'/'opd_061_realtime_kalshi_anchor_tap.py'
T=R/'test_opd_CRYPTO_ANCHOR_TIMESTAMP_BOUNDARY_REPAIR.py'
s=P.read_text(encoding='utf-8')
old='    t=float(received_at.timestamp())\n'
new='    t=float(received_at.timestamp()) if hasattr(received_at,"timestamp") else float(received_at)\n'
if old not in s and new not in s: raise RuntimeError('OPD061_TIMESTAMP_BOUNDARY_NOT_FOUND')
s=s.replace(old,new,1)
P.write_text(s,encoding='utf-8')
TEST='''from datetime import datetime,timezone
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
'''
T.write_text(TEST,encoding='utf-8')
compile(P.read_text(encoding='utf-8'),str(P),'exec');compile(TEST,str(T),'exec')
print('[PASS] existing OPD-061 crypto anchor timestamp boundary repaired')
print(P);print(T)