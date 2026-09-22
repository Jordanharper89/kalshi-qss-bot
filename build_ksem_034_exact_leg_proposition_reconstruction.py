from pathlib import Path
import json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem034_exact_leg_propositions.json"
TEST=ROOT/"test_ksem_034_exact_leg_proposition_reconstruction.py"

def main():
    print("="*120); print(" KSEM-034 EXACT LEG PROPOSITION RECONSTRUCTION"); print("="*120)
    rows=json.loads((S/"ksem033_underlying_sports_context.json").read_text())["rows"]
    out=[]
    for r in rows:
        m=r.get("underlying_market") or {}
        mt=(r.get("market_type") or {}).get("market_type")
        text=" | ".join(str(x) for x in (
            m.get("title"),m.get("yes_sub_title"),m.get("no_sub_title"),
            m.get("ticker"),m.get("event_ticker")) if x)
        out.append({"parent_ticker":r["parent_ticker"],"leg_index":r["leg_index"],
                    "market_ticker":r["market_ticker"],"event_ticker":r["event_ticker"],
                    "side":r["side"],"underlying_resolved":r["resolved"],
                    "league_candidates":r["league_candidates"],"market_type":mt,
                    "context_text":text})
    resolved=sum(x["underlying_resolved"] for x in out)
    league=sum(bool(x["league_candidates"]) for x in out)
    print("[LEGS]",len(out)); print("[UNDERLYING_RESOLVED]",resolved)
    print("[LEAGUE_CONTEXT_RECOVERED]",league)
    for x in out[:25]: print("[PROPOSITION]",x)
    if not out: raise RuntimeError("no reconstructed propositions")
    OUT.write_text(json.dumps({"rows":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem034_exact_leg_propositions.json').read_text())\nassert d['rows']\nassert all('context_text' in x for x in d['rows'])\nassert d['execution_authority'] is False\nprint('[PASS] exact leg propositions reconstructed from underlying market context')\nprint('[PASS] KSEM-034 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()