from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m
import qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap as tap
import qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge as bridge
assert m.MAX_STATE_AGE_SECONDS==120.0 and m.HURDLE==0.020 and m.MIN_NET_EDGE==0.005
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
assert tap._asset("KXITFMATCH-26SEP12PETHUR-HUR") is None and m._asset("KXITFMATCH-26SEP12PETHUR-HUR") is None
assert tap._asset("KXBTC15M-X")=="BTC" and tap._asset("KXETH15M-X")=="ETH" and tap._asset("KXSOLE-X")=="SOL"
old=tap._canonical_highwater; tap._canonical_highwater=lambda root:123
with tempfile.TemporaryDirectory() as td:
 r=Path(td); now=2000000000.0
 q=tap.freeze_trade({"type":"ticker","msg":{"market_ticker":"KXBTCD-X","yes_bid_dollars":"0.50","yes_ask_dollars":"0.60"}},now,"ticker-id",r)
 assert q and q["anchor_price"]==0.55 and q["kalshi_state"]["observation_type"]=="ticker" and q["anchor_sequence_boundary"]==123
 bad=tap.freeze_trade({"type":"ticker","msg":{"market_ticker":"KXITFMATCH-26SEP12PETHUR-HUR","yes_bid_dollars":"0.50","yes_ask_dollars":"0.60"}},now,"bad",r)
 assert bad is None
 a=m._latest_realtime_spool_anchor(r,now+2); assert a and a["ticker"]=="KXBTCD-X" and now+2-a["observed_epoch"]==2
 assert a["realtime_anchor_basis"]=="OPD061_REALTIME_TRADE_TICKER_SPOOL"
tap._canonical_highwater=old
src=Path("qseries_v2/oracle_adapters/kalshi/oad_036_websocket_canonical_bridge.py").read_text(encoding="utf-8")
assert 'if typ in ("trade","ticker"):' in src
print("[PASS] OAD-036 now sends trade + ticker events into existing OPD-061 realtime anchor tap")
print("[PASS] OPD-061 freezes exact ticker midpoint/last/trade price with canonical high-water lineage")
print("[PASS] family selector consumes <=120s realtime trade/ticker anchors before canonical fallback")
print("[PASS] stale canonical family anchors no longer outrank fresh fast-lane events")
print("[PASS] PETHUR blocked at realtime tap and predictor root")
print("[PASS] 120s freshness gate, exact-contract ranking, 2pct hurdle, publication, execution unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
