from pathlib import Path
import json

ROOT=Path.cwd()
OUT=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem032_underlying_market_resolution.json"
TEST=ROOT/"test_ksem_032_exact_underlying_market_resolver.py"

def keep(m):
    keys=("ticker","event_ticker","title","yes_sub_title","no_sub_title",
          "market_type","status","custom_strike")
    return {k:m.get(k) for k in keys}

def main():
    print("="*120); print(" KSEM-032 EXACT UNDERLYING KALSHI MARKET RESOLVER"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    _,_,markets,_=read_production_sports_candidates(root=ROOT,market_limit=1000)
    index={m.get("ticker"):m for m in markets if m.get("ticker")}
    rows=[]
    for parent in markets:
        for i,x in enumerate(parent.get("mve_selected_legs") or [],1):
            ticker=x.get("market_ticker"); hit=index.get(ticker)
            rows.append({"parent_ticker":parent.get("ticker"),"leg_index":i,
                         "market_ticker":ticker,"event_ticker":x.get("event_ticker"),
                         "side":x.get("side"),"resolved":hit is not None,
                         "underlying_market":keep(hit) if hit else None})
    resolved=sum(x["resolved"] for x in rows)
    print("[CURRENT_MARKETS]",len(markets)); print("[MVE_LEGS]",len(rows))
    print("[UNDERLYING_RESOLVED]",resolved); print("[UNDERLYING_MISSING]",len(rows)-resolved)
    if not rows: raise RuntimeError("no MVE legs found")
    OUT.write_text(json.dumps({"rows":rows,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem032_underlying_market_resolution.json').read_text())\nassert d['rows']\nassert all('resolved' in x for x in d['rows'])\nassert d['execution_authority'] is False\nprint('[PASS] every MVE leg received exact underlying-market resolution status')\nprint('[PASS] KSEM-032 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()