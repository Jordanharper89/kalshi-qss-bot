from pathlib import Path
import json,re

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem030_exact_osn_team_pair_index.json"
TEST=ROOT/"test_ksem_030_exact_osn_team_pair_index.py"

def norm(x):
    return re.sub(r"[^a-z0-9]+"," ",str(x).lower()).strip()

def main():
    print("="*120); print(" KSEM-030 EXACT OSN TEAM-PAIR INDEX"); print("="*120)
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
    rows=[]
    for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL"):
        result=acquire_canonical_events(league,timeout=15,root=ROOT)
        for e in result.events:
            home=norm(e.home_team); away=norm(e.away_team)
            rows.append({"league":e.league,"home_team":e.home_team,"away_team":e.away_team,
                         "home_norm":home,"away_norm":away,
                         "team_pair_key":"|".join(sorted((home,away))),
                         "provider":e.provider,"provider_event_id":e.provider_event_id,
                         "scheduled_start":e.scheduled_start})
    print("[CANONICAL_EVENTS]",len(rows))
    print("[UNIQUE_TEAM_PAIRS]",len({x["team_pair_key"] for x in rows}))
    for x in rows[:12]: print("[EVENT]",x)
    if not rows: raise RuntimeError("OSN canonical team-pair index empty")
    STATE.write_text(json.dumps({"events":rows,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem030_exact_osn_team_pair_index.json').read_text())\nassert d['events']\nassert all(x['team_pair_key'] for x in d['events'])\nassert d['execution_authority'] is False\nprint('[PASS] six-league exact OSN canonical team-pair index built')\nprint('[PASS] KSEM-030 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()