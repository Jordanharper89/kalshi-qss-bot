from pathlib import Path
import json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem036_residual_gap_root_causes.json"
TEST=ROOT/"test_ksem_036_residual_gap_root_cause_gate.py"
ADMITTED={"NFL","NCAAF","NBA","NHL","MLS","EPL"}

def reason(r):
    if r["status"]=="EXACT_CONTEXT_BOUND": return "EXACT_CONTEXT_BOUND"
    if r["status"]=="AMBIGUOUS": return "AMBIGUOUS_CANONICAL_EVENT"
    if not r["underlying_resolved"]: return "UNDERLYING_MARKET_NOT_RESOLVED"
    if not r["league_candidates"]: return "LEAGUE_CONTEXT_UNRESOLVED"
    if not any(x in ADMITTED for x in r["league_candidates"]): return "SOURCE_NOT_ADMITTED"
    if len([x for x in r["league_candidates"] if x in ADMITTED])>1: return "MULTIPLE_SUPPORTED_LEAGUES"
    return "NO_EXACT_CANONICAL_EVENT_MATCH"

def main():
    print("="*120); print(" KSEM-036 RESIDUAL GAP ROOT-CAUSE GATE"); print("="*120)
    rows=json.loads((S/"ksem035_contextual_osn_binding.json").read_text())["rows"]
    out=[{**r,"root_cause":reason(r)} for r in rows]
    counts={}
    for r in out: counts[r["root_cause"]]=counts.get(r["root_cause"],0)+1
    print("[TOTAL]",len(out))
    for k,v in sorted(counts.items(),key=lambda x:(-x[1],x[0])): print("[ROOT_CAUSE]",k,v)
    if sum(counts.values())!=len(out): raise RuntimeError("root-cause accounting failure")
    OUT.write_text(json.dumps({"total":len(out),"counts":counts,"rows":out,
                               "execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem036_residual_gap_root_causes.json').read_text())\nassert d['total']>0\nassert sum(d['counts'].values())==d['total']\nassert d['execution_authority'] is False\nprint('[PASS] every contextual binding result has an exact residual root cause')\nprint('[PASS] KSEM-036 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()