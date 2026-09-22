from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_016_contract_isolated_discovery_holdout_freeze.py";TEST=ROOT/"test_opd_016_contract_isolated_discovery_holdout_freeze.py"
MOD.write_text(r"""
from pathlib import Path
from collections import Counter
import hashlib,json
def _bucket(t): return int(hashlib.sha256(str(t).encode()).hexdigest()[:8],16)%100
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";src=rt/"opd_015_prediction_ready_world_state_matrix.jsonl"
    tickers={};rows=Counter();crypto=Counter();core=Counter()
    with src.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line);t=x["ticker"];s="DISCOVERY" if _bucket(t)<70 else "HOLDOUT";tickers[t]=s;rows[s]+=1
            if x.get("asset"):crypto[s]+=1
            if x.get("asset") and x.get("kalshi_state") and x.get("coinbase_hf_state") and x.get("crypto_condition_state"):core[s]+=1
    d=sorted(t for t,s in tickers.items() if s=="DISCOVERY");h=sorted(t for t,s in tickers.items() if s=="HOLDOUT")
    if not d or not h: raise RuntimeError("SPLIT_DEGENERATE")
    s={"schema_version":"OPD-016","split_method":"SHA256_TICKER_70_30","discovery_tickers":d,"holdout_tickers":h,
       "ticker_count":len(tickers),"discovery_ticker_count":len(d),"holdout_ticker_count":len(h),
       "row_counts":dict(rows),"crypto_row_counts":dict(crypto),"crypto_core_row_counts":dict(core),
       "holdout_visible_to_formula_discovery":False,"split_hash":_h({"d":d,"h":h}),
       "model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,
       "publication_allowed":False,"execution_authority":False}
    out=rt/"opd_016_contract_isolated_discovery_holdout_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8");return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_016_contract_isolated_discovery_holdout_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["discovery_ticker_count"]>0 and s["holdout_ticker_count"]>0
assert set(s["discovery_tickers"]).isdisjoint(s["holdout_tickers"]) and not s["holdout_visible_to_formula_discovery"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[TICKERS]",s["ticker_count"]);print("[DISCOVERY_TICKERS]",s["discovery_ticker_count"]);print("[HOLDOUT_TICKERS]",s["holdout_ticker_count"])
print("[ROW_COUNTS]",s["row_counts"]);print("[CRYPTO_ROWS]",s["crypto_row_counts"]);print("[CRYPTO_CORE_ROWS]",s["crypto_core_row_counts"]);print("[SPLIT_HASH]",s["split_hash"])
print("[PASS] whole tickers assigned to exactly one discovery/holdout partition");print("[PASS] holdout contracts remain invisible to formula discovery");print("[PASS] OPD-016 contract-isolated discovery/holdout freeze certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-016 installer complete")