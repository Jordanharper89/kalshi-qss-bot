from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state"
MOD=PKG/"exact_live_underlying_market_retrieval.py"
TEST=ROOT/"test_ksem_061_exact_live_underlying_market_retrieval.py"

MODULE = r"""
from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _ticker(m):
    return str(m.get("ticker","") or "").strip()

def _legs(m):
    rows=m.get("mve_selected_legs") or ()
    return tuple(x for x in rows if isinstance(x,dict))

def _raw_market(response):
    body=getattr(response,"body",None)
    if not isinstance(body,dict):
        return None
    raw=body.get("market") if isinstance(body.get("market"),dict) else body
    return raw if isinstance(raw,dict) else None

def select_current_mve_underlying_tickers(root=None,limit=1000,max_tickers=50,timeout_seconds=20):
    root=Path(root or Path.cwd()).resolve()
    markets,_=fetch_current_open_kalshi_market_index(root=root,limit=limit,timeout_seconds=timeout_seconds)
    out=[]; seen=set()
    for parent in markets:
        for leg in _legs(parent):
            ticker=str(leg.get("market_ticker") or "").strip().upper()
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            out.append({
                "parent_ticker":_ticker(parent),
                "leg_index":leg.get("leg_index"),
                "event_ticker":str(leg.get("event_ticker") or "").strip().upper(),
                "market_ticker":ticker,
                "side":str(leg.get("side") or "").strip().lower(),
            })
            if len(out)>=int(max_tickers):
                return tuple(out)
    return tuple(out)

def retrieve_exact_market(credentials,ticker,timeout_seconds=10):
    ticker=str(ticker or "").strip().upper()
    if not ticker:
        return None
    response=kalshi_rest_get(credentials,f"/markets/{ticker}",{},timeout_seconds)
    raw=_raw_market(response)
    if raw is None:
        return None
    actual=str(raw.get("ticker") or raw.get("market_ticker") or "").strip().upper()
    if actual!=ticker:
        return None
    return dict(raw)

def run_physical_gate(root=None,max_tickers=25,timeout_seconds=15):
    root=Path(root or Path.cwd()).resolve()
    legs=select_current_mve_underlying_tickers(root=root,max_tickers=max_tickers,timeout_seconds=timeout_seconds)
    if not legs:
        raise RuntimeError("NO_CURRENT_MVE_UNDERLYING_TICKERS")
    credentials=load_kalshi_credentials(root=root)
    rows=[]
    for leg in legs:
        ticker=leg["market_ticker"]
        try:
            market=retrieve_exact_market(credentials,ticker,timeout_seconds)
            status="RESOLVED" if market else "NOT_FOUND"
            error=""
        except Exception as exc:
            market=None; status="ERROR"; error=f"{type(exc).__name__}: {exc}"
        rows.append({**leg,"status":status,"market":market,"error":error})
    return tuple(rows)
"""

TEST_BODY = r"""
from pathlib import Path
import json
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_underlying_market_retrieval import run_physical_gate

root=Path.cwd()
rows=run_physical_gate(root=root,max_tickers=25,timeout_seconds=15)
counts={k:sum(r["status"]==k for r in rows) for k in ("RESOLVED","NOT_FOUND","ERROR")}
print("[ROWS]",len(rows))
print("[COUNTS]",counts)
for r in rows[:10]:
    print("[SAMPLE]",r["market_ticker"],r["status"])
assert rows
assert counts["RESOLVED"]>0, "no current MVE underlying ticker resolved through exact Kalshi GET"
assert counts["ERROR"]==0, f"transport errors present: {counts}"
state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
state.mkdir(parents=True,exist_ok=True)
(state/"ksem061_exact_live_underlying_market_retrieval.json").write_text(
    json.dumps({"rows":rows,"counts":counts,"execution_authority":False},indent=2,default=str),
    encoding="utf-8")
print("[PASS] current MVE underlying markets physically resolved by exact ticker")
print("[PASS] KSEM-061 certified")
"""

def main():
    print("="*120)
    print(" KSEM-061 EXACT LIVE UNDERLYING MARKET RETRIEVAL INSTALLER")
    print("="*120)
    PKG.mkdir(parents=True,exist_ok=True); STATE.mkdir(parents=True,exist_ok=True)
    MOD.write_text(MODULE.lstrip(),encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT))
    print("[PASS] wrote",TEST.name)
    print("[PASS] read-only OAD-021 -> OAD-022 exact-market path bound directly")
    print("[PASS] no OPL settlement normalization used")
    print("[PASS] KSEM-061 installer complete")
if __name__=="__main__":
    main()
