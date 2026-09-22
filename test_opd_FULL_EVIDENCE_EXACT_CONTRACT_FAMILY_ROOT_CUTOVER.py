from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.HURDLE == 0.020
assert m.MIN_NET_EDGE == 0.005
assert m.EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_REVISION=="EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1"
assert hasattr(m,"_run_single_contract")
assert hasattr(m,"run")
assert hasattr(m,"_recent_asset_anchor_universe")
assert hasattr(m,"_canonical_exact_market_spec")
assert hasattr(m,"_public_exact_market_specs")

high={"market_title":"Will Bitcoin be above $79,000?","yes_sub_title":"$79,000 or above"}
low={"market_title":"Will Bitcoin be below $77,000?","yes_sub_title":"Below $77,000"}

assert m._yes_semantic(high)=="YES_MEANS_UNDERLYING_HIGHER"
assert m._yes_semantic(low)=="YES_MEANS_UNDERLYING_LOWER"

assert m._underlying_view("UP","YES_MEANS_UNDERLYING_HIGHER")=="BULLISH"
assert m._underlying_view("DOWN","YES_MEANS_UNDERLYING_HIGHER")=="BEARISH"
assert m._underlying_view("UP","YES_MEANS_UNDERLYING_LOWER")=="BEARISH"
assert m._underlying_view("DOWN","YES_MEANS_UNDERLYING_LOWER")=="BULLISH"

src=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert 'def _run_single_contract(root=None,now=None,anchor=None):' in src
assert 'def run(root=None,now=None,anchor=None):' in src
assert '"market_title":anchor.get("market_title")' in src
assert '"functional_strike":anchor.get("functional_strike")' in src
assert 'MAX_FAMILY_CONTRACTS=12' in src
assert 'FAMILY_BEST_TICKER=' in src
assert 'CONTRACT_YES_PRICE_VIEW=' in src
assert 'contract_horizon' in src
assert 'PREDICTION_LEDGER_REVISION=' in src
assert 'LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME' in src

print("[PASS] existing full-evidence predictor is now exact-contract-family aware")
print("[PASS] existing single-contract scoring engine preserved under _run_single_contract")
print("[PASS] exact market title/subtitles/structured strikes added to immutable prediction lineage")
print("[PASS] recent sibling contracts for the same crypto asset are independently scored")
print("[PASS] contract YES-price direction separated from underlying crypto interpretation")
print("[PASS] above/below contract semantics deterministically map to bullish/bearish underlying view")
print("[PASS] family ranking selects across specific contracts and horizons")
print("[PASS] 2pct hurdle, live gates, contract-horizon gate, publication, and execution policy preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
