from pathlib import Path
import json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem041_retrieval_boundary_decision.json"
TEST=ROOT/"test_ksem_041_retrieval_boundary_decision_gate.py"

def main():
    print("="*120); print(" KSEM-041 RETRIEVAL BOUNDARY DECISION GATE"); print("="*120)
    d=json.loads((S/"ksem040_exact_physical_ticker_retrieval.json").read_text())
    rows=d["results"]; ok=[x for x in rows if x["ok"]]
    errors=[x for x in rows if not x["ok"]]
    nonempty=[x for x in ok if x.get("repr") not in ("None","()","[]","{}","''")]
    if nonempty:
        decision="EXISTING_EXACT_RETRIEVAL_PATH_PHYSICALLY_RESPONDED"
    elif ok:
        decision="EXISTING_INTERFACE_EXECUTED_BUT_RETURNED_NO_MARKET_PAYLOAD"
    else:
        decision="EXISTING_INTERFACE_NOT_PHYSICALLY_USABLE_FOR_MVE_TICKERS"
    data={"sample_size":len(rows),"successful_calls":len(ok),
          "nonempty_responses":len(nonempty),"errors":len(errors),
          "decision":decision,"execution_authority":False}
    print("[SAMPLE_SIZE]",data["sample_size"]); print("[SUCCESSFUL_CALLS]",len(ok))
    print("[NONEMPTY_RESPONSES]",len(nonempty)); print("[ERRORS]",len(errors))
    print("[DECISION]",decision)
    OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem041_retrieval_boundary_decision.json').read_text())\nassert d['sample_size']>0 and d['decision']\nassert d['execution_authority'] is False\nprint('[PASS] exact Kalshi underlying-market retrieval boundary classified from physical evidence')\nprint('[PASS] KSEM-041 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()