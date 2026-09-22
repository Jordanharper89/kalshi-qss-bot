from pathlib import Path
import tempfile,json
import qseries_v2.oracle_predictive_discovery.opd_live_prediction_now as m

def fake_tokens(root,state):
    z={"H:"+str(state["horizon_seconds"]),"K:ANCHOR_PRICE:40_50C"}
    if state.get("coinbase_hf_state"):z.add("CB:60:RET:GE_20BPS")
    return tuple(z)
m.materialize_exact_live_tokens=fake_tokens
a={"anchor_id":"a1","ticker":"KXBTC","asset":"BTC","observed_epoch":1.0,"anchor_price":0.45,"kalshi_state":{}}
freeze={"candidates":[{"family_id":"f1","horizon_seconds":60,"target":"RETURN_POS",
"formula":["H:60","K:ANCHOR_PRICE:40_50C","CB:60:RET:GE_20BPS"],
"historical_net_after_hurdle":0.03,"historical_holdout_lift":0.2,"historical_holdout_q":0.01}]}
assert m._plausible(a,freeze["candidates"],Path.cwd()) is True
extra={"coinbase_hf_state":{"60":{"return":0.01}},"crypto_condition_state":{},"learned_state":None}
z=m.select_signal(a,freeze,[],extra,Path.cwd())
assert z and z["family_id"]=="f1" and z["certified"] is False
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/"x.jsonl"
 p.write_text("\n".join(json.dumps(dict(a,anchor_id=f"a{i}")) for i in range(40)),encoding="utf-8")
 rows=m._tail_anchors(p,max_anchors=7,max_bytes=1048576)
 assert len(rows)==7 and rows[0]["anchor_id"]=="a39"
print("[PASS] bounded multi-anchor live scan + static prefilter + frozen-formula selector")
print("[EXECUTION_AUTHORITY] FALSE")
