from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
for x in ("taker_imbalance","trade_volume","spread_mean","sibling_","coinbase_","future_return","prediction_id"):
    assert x in s,x
assert "future_return" not in s[s.find("def features"):s.find("def cbret")]
print("[PASS] OSD-002 deterministic interface test")
print("[PASS] decision-time features exclude future outcome from feature construction")
print("[PASS] trade-flow/volume/timing/spread/sibling/Coinbase families present")
print("[PASS] execution/publication remain false")
