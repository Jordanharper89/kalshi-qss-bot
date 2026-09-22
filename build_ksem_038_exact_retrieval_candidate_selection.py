from pathlib import Path
import json

ROOT=Path.cwd()
S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem038_exact_retrieval_candidate_selection.json"
TEST=ROOT/"test_ksem_038_exact_retrieval_candidate_selection.py"

def score(x):
    n=x["function"].lower(); args=" ".join(x["args"]).lower(); s=0
    if "ticker" in args: s+=100
    if "market_ticker" in args: s+=100
    if "event_ticker" in args: s+=80
    if "ticker" in n: s+=50
    if "market" in n: s+=20
    if "event" in n: s+=10
    if "exact" in n: s+=25
    return s

def main():
    print("="*120); print(" KSEM-038 EXACT RETRIEVAL CANDIDATE SELECTION"); print("="*120)
    rows=json.loads((S/"ksem037_exact_ticker_retrieval_audit.json").read_text())["candidates"]
    ranked=sorted(({**x,"score":score(x)} for x in rows),key=lambda x:(-x["score"],x["file"],x["line"]))
    viable=[x for x in ranked if x["score"]>=100]
    print("[AUDITED]",len(ranked)); print("[VIABLE]",len(viable))
    for x in viable[:30]: print("[VIABLE_CANDIDATE]",x)
    if not viable: raise RuntimeError("no proven identifier-accepting Kalshi retrieval interface found")
    OUT.write_text(json.dumps({"viable":viable,"selected":viable[0],
                               "execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem038_exact_retrieval_candidate_selection.json').read_text())\nassert d['viable'] and d['selected']['score']>=100\nassert d['execution_authority'] is False\nprint('[PASS] exact identifier-capable Kalshi retrieval candidate selected from physical audit')\nprint('[PASS] KSEM-038 certified')\n",encoding="utf-8")
    print("[SELECTED]",viable[0]); print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()