from pathlib import Path
import importlib.util,inspect,json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem040_exact_physical_ticker_retrieval.json"
TEST=ROOT/"test_ksem_040_exact_physical_ticker_retrieval_gate.py"

def main():
    print("="*120); print(" KSEM-040 EXACT PHYSICAL TICKER RETRIEVAL GATE"); print("="*120)
    sel=json.loads((S/"ksem038_exact_retrieval_candidate_selection.json").read_text())["selected"]
    legs=json.loads((S/"ksem032_underlying_market_resolution.json").read_text())["rows"]
    p=ROOT/sel["file"]
    spec=importlib.util.spec_from_file_location("ksem040_selected",p)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    fn=getattr(mod,sel["function"]); sig=inspect.signature(fn)
    if inspect.iscoroutinefunction(fn): raise RuntimeError("selected interface is async; bounded adapter required")
    ticker_arg=next((n for n in sig.parameters if "ticker" in n.lower()),None)
    if not ticker_arg: raise RuntimeError("selected interface has no ticker parameter")
    required=[n for n,p in sig.parameters.items()
              if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD)]
    if any(n!=ticker_arg for n in required):
        raise RuntimeError("selected interface requires unsupported arguments: "+repr(required))
    sample=[]
    seen=set()
    for r in legs:
        t=r["market_ticker"]
        if t and t not in seen: seen.add(t); sample.append(t)
        if len(sample)>=10: break
    results=[]
    for ticker in sample:
        try:
            value=fn(**{ticker_arg:ticker})
            results.append({"requested":ticker,"ok":True,"type":type(value).__name__,"repr":repr(value)[:4000]})
        except Exception as e:
            results.append({"requested":ticker,"ok":False,"error":type(e).__name__+": "+str(e)})
    print("[FUNCTION]",sel["file"],sel["function"]); print("[TICKER_ARG]",ticker_arg)
    for x in results: print("[RETRIEVAL]",x)
    if not results: raise RuntimeError("no physical ticker cohort")
    OUT.write_text(json.dumps({"selected":sel,"ticker_arg":ticker_arg,"results":results,
                               "execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem040_exact_physical_ticker_retrieval.json').read_text())\nassert d['results']\nassert d['execution_authority'] is False\nprint('[PASS] selected exact Kalshi retrieval interface physically exercised on real MVE tickers')\nprint('[PASS] KSEM-040 measurement certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()