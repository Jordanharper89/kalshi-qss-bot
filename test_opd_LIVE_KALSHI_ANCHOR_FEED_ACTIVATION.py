from datetime import datetime,timezone
import qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge as m
calls=[]
def fake(raw,received_at,observation_id,root=None):
    calls.append((raw,received_at,observation_id,root));return {"anchor_id":"x"}
m.freeze_trade=fake
t=datetime(2026,9,11,21,0,0,tzinfo=timezone.utc)
trade={"type":"trade","sid":1,"seq":2,"msg":{"market_ticker":"KXBTC15M-TEST","yes_price_dollars":"0.55"}}
o=m.build_ola_canonical_observation_from_websocket(trade,received_at=t,acquisition_batch_id="batch.test")
assert len(calls)==1 and calls[0][2]==o.observation_id
ticker={"type":"ticker","sid":1,"seq":3,"msg":{"market_ticker":"KXBTC15M-TEST","price_dollars":"0.56"}}
m.build_ola_canonical_observation_from_websocket(ticker,received_at=t,acquisition_batch_id="batch.test2")
assert len(calls)==1
print("[PASS] OAD-036 live trade bridge now feeds OPD-061 anchor freeze exactly once per trade")
print("[PASS] non-trade websocket events do not create predictive anchors")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
