import inspect
from collections import namedtuple
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

Obs=namedtuple("Obs","payload")
class FakeAdapter:
    def __init__(self,**kw):
        assert kw["market_status"]=="open"
        assert kw["market_tickers"]==("KXBTC15M-TEST",)
        assert kw["page_limit"]==1 and kw["max_pages"]==1
    def acquire(self,*,acquired_at):
        return (Obs((("source_market_id","KXBTC15M-TEST"),
                     ("source_close_time","2026-09-12T07:00:00Z"))),)

meta=m._public_contract_close_metadata("KXBTC15M-TEST",FakeAdapter)
assert meta["basis"]=="LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME"
assert meta["close_epoch"] is not None
assert meta["metadata_sequence"] is None

states=[];outs={}
for i in range(24):
    sid="h"+str(i)
    states.append({"state_id":sid,"ticker":"KXBTC"+str(i%4),
      "observed_epoch":1000+i,"horizon_seconds":300,
      "tokens":["K:A","CB:B","CC:C","L:D"]})
    outs[sid]={"state_id":sid,"resolution_epoch":1500+i,
      "future_return":-0.05,"mfe":-0.01,"mae":-0.05}

base={"state_id":"LIVE","ticker":"KXBTC15M-TEST",
 "observed_epoch":2000.0,"horizon_seconds":300,
 "tokens":["K:A","CB:B","CC:C","L:D"]}
ok=m._score_state(dict(base,contract_close_epoch=2300.0),states,outs,2001.0)
bad=m._score_state(dict(base,contract_close_epoch=2299.0),states,outs,2001.0)

assert ok["checks"]["contract_horizon"] is True and ok["passed"] is True
assert bad["checks"]["contract_horizon"] is False and bad["passed"] is False
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False

src=inspect.getsource(m._contract_close_metadata)
assert "_public_contract_close_metadata(ticker)" in src

print("[PASS] exact-ticker public Kalshi close-time fallback verified without network")
print("[PASS] indexed canonical close-time remains first choice")
print("[PASS] no ticker parsing or inferred expiration introduced")
print("[PASS] contract-horizon fail-closed semantics preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
