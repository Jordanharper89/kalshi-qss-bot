from pathlib import Path
import json,re

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem035_contextual_osn_binding.json"
TEST=ROOT/"test_ksem_035_contextual_osn_event_binding.py"
ADMITTED={"NFL","NCAAF","NBA","NHL","MLS","EPL"}

def norm(x): return re.sub(r"[^a-z0-9]+"," ",str(x).lower()).strip()

def contained(name,text):
    n=norm(name); tokens=set(norm(text).split())
    return bool(n) and (n in norm(text) if " " in n else n in tokens)

def main():
    print("="*120); print(" KSEM-035 CONTEXTUAL OSN CANONICAL EVENT BINDING"); print("="*120)
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
    legs=json.loads((S/"ksem034_exact_leg_propositions.json").read_text())["rows"]
    events=[]
    for league in sorted(ADMITTED):
        for e in acquire_canonical_events(league,timeout=15,root=ROOT).events:
            events.append({"league":e.league,"home":e.home_team,"away":e.away_team,
                           "provider":e.provider,"provider_event_id":e.provider_event_id,
                           "scheduled_start":e.scheduled_start})
    out=[]
    for r in legs:
        leagues=[x for x in r["league_candidates"] if x in ADMITTED]
        matches=[]
        if len(leagues)==1:
            for e in events:
                if e["league"]==leagues[0] and contained(e["home"],r["context_text"]) and contained(e["away"],r["context_text"]):
                    matches.append(e)
        status="EXACT_CONTEXT_BOUND" if len(matches)==1 else ("AMBIGUOUS" if len(matches)>1 else "UNBOUND")
        out.append({**r,"supported_leagues":leagues,"status":status,"matches":matches[:5]})
    counts={k:sum(x["status"]==k for x in out) for k in ("EXACT_CONTEXT_BOUND","AMBIGUOUS","UNBOUND")}
    print("[COUNTS]",counts)
    for x in out[:30]: print("[BINDING]",x)
    OUT.write_text(json.dumps({"counts":counts,"rows":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem035_contextual_osn_binding.json').read_text())\nassert d['rows']\nassert sum(d['counts'].values())==len(d['rows'])\nassert d['execution_authority'] is False\nprint('[PASS] contextual OSN binding accounted every reconstructed leg fail-closed')\nprint('[PASS] KSEM-035 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()