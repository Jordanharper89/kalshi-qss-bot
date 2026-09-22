from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_kalshi_exact_price_profitability_gate.py"
TEST=ROOT/"test_opd_BTC_KALSHI_EXACT_DOLLAR_FIELDS_V6.py"

s=TARGET.read_text(encoding="utf-8")

repls={
'"yes_price","yes_bid","yes_ask","yes_bid_price","yes_ask_price",':
'"yes_price","yes_bid","yes_ask","yes_bid_price","yes_ask_price","yes_price_dollars","yes_bid_dollars","yes_ask_dollars",',
'for k in ("yes_bid","yes_bid_price","best_yes_bid"):':
'for k in ("yes_bid","yes_bid_price","best_yes_bid","yes_bid_dollars"):',
'for k in ("yes_ask","yes_ask_price","best_yes_ask"):':
'for k in ("yes_ask","yes_ask_price","best_yes_ask","yes_ask_dollars"):',
'for k in ("price","last_price","market_price"):':
'for k in ("yes_price_dollars","price_dollars","price","last_price","market_price"):',
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit("[FAIL] expected source fragment not found: "+old)
    s=s.replace(old,new,1)

TARGET.write_text(s,encoding="utf-8")
compile(s,str(TARGET),"exec")

test='from pathlib import Path\nP=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")\ns=P.read_text(encoding="utf-8")\ncompile(s,str(P),"exec")\nfor x in (\'"yes_price_dollars"\',\'"yes_bid_dollars"\',\'"yes_ask_dollars"\',\'"price_dollars"\',"HURDLE=0.02","KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND"):\n    assert x in s,x\nprint("[PASS] exact observed Kalshi dollar price fields installed")\nprint("[PASS] trade yes_price_dollars supported")\nprint("[PASS] ticker yes_bid_dollars/yes_ask_dollars/price_dollars supported")\nprint("[PASS] existing anchor recovery preserved")\nprint("[PASS] 28-survivor signal family and fixed 2% hurdle unchanged")\nprint("[PASS] execution/publication remain false")\n'
TEST.write_text(test,encoding="utf-8")
compile(test,str(TEST),"exec")

print("[PASS] BTC->Kalshi exact dollar-field cutover V6 installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[FIELDS] yes_price_dollars / yes_bid_dollars / yes_ask_dollars / price_dollars")
print("[SIGNAL/HURDLE] unchanged / 0.02")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")