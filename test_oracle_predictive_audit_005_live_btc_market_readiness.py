from collections import Counter
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from qseries_v2.oracle_adapters.independent.oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings
from qseries_v2.oracle_adapters.independent.oad_244_crypto_physical_ocl006_exact_calibration import materialize_exact_prospective_calibration

markets,_=fetch_current_open_kalshi_market_index(limit=1000,timeout_seconds=20)
btc=[]
for m in markets:
    text=" ".join(str(m.get(k,"") or "") for k in
                  ("ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title")).upper()
    if "BTC" in text or "BITCOIN" in text:
        btc.append(m)

learned=read_crypto_learned_case_history(assets=("BTC",),per_asset_limit=512)
bindings=[x for x in read_exact_prospective_bindings() if x.asset=="BTC"]
cal=materialize_exact_prospective_calibration()

print("[OPEN_MARKETS_TOTAL]",len(markets))
print("[OPEN_BTC_MARKETS]",len(btc))
print("[BTC_LEARNED_CASES]",len(learned))
print("[BTC_EXACT_LEARNED]",sum(bool(x.exact_interval) for x in learned))
print("[BTC_FORWARD_BINDINGS]",len(bindings))
print("[GLOBAL_EXACT_CALIBRATION_CASES]",cal.scored_cases)
for m in btc[:30]:
    view={k:m.get(k) for k in ("ticker","event_ticker","title","subtitle",
          "yes_sub_title","no_sub_title","yes_bid","yes_ask","last_price",
          "close_time","expiration_time","status") if k in m}
    print("[BTC_MARKET]",view)

families=Counter()
for m in btc:
    t=str(m.get("ticker","")).upper()
    if "15M" in t: families["15M"]+=1
    elif "BTCY" in t: families["YEAR_THRESHOLD"]+=1
    else: families["OTHER"]+=1
print("[BTC_FAMILIES]",dict(families))
assert markets,"Kalshi open-market response empty"
print("[PASS] OPA-005 live BTC market readiness audit complete")
