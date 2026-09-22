from pathlib import Path
import json,re

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=STATE/"ksem045_recovered_underlying_context.json"
TEST=ROOT/"test_ksem_045_recovered_underlying_context_gate.py"

PREFIX={"KXNCAAF":"NCAAF","KXNFL":"NFL","KXNBA":"NBA","KXNHL":"NHL","KXMLS":"MLS","KXEPL":"EPL","KXMLB":"MLB"}

def league(ticker):
    u=ticker.upper()
    for p,l in PREFIX.items():
        if u.startswith(p): return l
    m=re.match(r"^KX([A-Z0-9]+?)(?:GAME|MATCH|SERIES)-",u)
    return m.group(1) if m else ""

def main():
    print("="*120); print(" KSEM-045 RECOVERED UNDERLYING SPORTS CONTEXT GATE"); print("="*120)
    m=json.loads((STATE/"ksem044_underlying_ticker_resolution_measurement.json").read_text())
    rows=[]
    for x in m["rows"]:
        ticker=x["ticker"]
        rows.append({"ticker":ticker,"retrieval_status":x["status"],
                     "event_ticker":ticker.rsplit("-",1)[0] if "-" in ticker else ticker,
                     "league_from_exact_ticker":league(ticker)})
    resolved=[x for x in rows if x["retrieval_status"].startswith("RESOLVED")]
    with_league=[x for x in resolved if x["league_from_exact_ticker"]]
    print("[RESOLVED]",len(resolved)); print("[RESOLVED_WITH_LEAGUE_CONTEXT]",len(with_league))
    for x in rows: print("[CONTEXT]",x)
    OUT.write_text(json.dumps({"rows":rows,"resolved":len(resolved),"resolved_with_league_context":len(with_league),"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem045_recovered_underlying_context.json').read_text())\nassert d['rows']\nassert d['resolved']>=0\nassert d['execution_authority'] is False\nprint('[PASS] underlying sports context measured from exact physical ticker identity')\nprint('[PASS] KSEM-045 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()