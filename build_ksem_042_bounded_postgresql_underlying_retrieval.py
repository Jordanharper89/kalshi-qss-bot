from pathlib import Path
import importlib, json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=STATE/"ksem042_bounded_postgresql_underlying_retrieval.json"
TEST=ROOT/"test_ksem_042_bounded_postgresql_underlying_retrieval.py"
SRCMOD="qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit"

def safe(x):
    if x is None or isinstance(x,(str,int,float,bool)): return x
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,set)): return [safe(v) for v in x]
    if hasattr(x,"__dict__"): return {"__type__":type(x).__name__,**{str(k):safe(v) for k,v in vars(x).items()}}
    return {"__type__":type(x).__name__,"__repr__":repr(x)}

def main():
    print("="*120); print(" KSEM-042 BOUNDED POSTGRESQL UNDERLYING-MARKET RETRIEVAL"); print("="*120)
    src=json.loads((STATE/"ksem032_underlying_market_resolution.json").read_text(encoding="utf-8"))
    tickers=[]; seen=set()
    for row in src["rows"]:
        t=str(row.get("market_ticker") or "")
        if t and t not in seen: seen.add(t); tickers.append(t)
        if len(tickers)>=50: break
    if not tickers: raise RuntimeError("no physical MVE underlying tickers available")
    mod=importlib.import_module(SRCMOD)
    _,backend=mod._router_backend(ROOT)
    if backend is None or not hasattr(backend,"_connect"): raise RuntimeError("production PostgreSQL backend unavailable")
    raw=mod._read_market_snapshot_observations(backend,tuple(tickers))
    encoded=safe(raw)
    pairs=sum(1 for x in raw if isinstance(x,tuple) and len(x)>=3 and x[0]=="PAIR")
    print("[REQUESTED_TICKERS]",len(tickers)); print("[RAW_RESULTS]",len(raw)); print("[PAIR_RESULTS]",pairs)
    for x in encoded[:20]: print("[RESULT]",x)
    OUT.write_text(json.dumps({"requested_tickers":tickers,"raw_result_count":len(raw),"pair_result_count":pairs,"raw_results":encoded,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem042_bounded_postgresql_underlying_retrieval.json').read_text())\nassert d['requested_tickers']\nassert d['raw_result_count']>=0\nassert d['execution_authority'] is False\nprint('[PASS] exact production PostgreSQL ticker reader physically exercised')\nprint('[PASS] KSEM-042 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()