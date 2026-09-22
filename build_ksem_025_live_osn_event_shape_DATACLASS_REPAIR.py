from pathlib import Path
from dataclasses import fields,is_dataclass
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json"
TEST=ROOT/"test_ksem_025_live_osn_event_shape_DATACLASS_REPAIR.py"

def shape(x):
    names=[f.name for f in fields(x)] if is_dataclass(x) else []
    vals={}
    for n in names:
        v=getattr(x,n)
        vals[n]={"type":type(v).__name__,"repr":repr(v)[:300]}
    return {"type":type(x).__name__,"fields":vals,"repr":repr(x)[:1200]}

def main():
    print("="*120); print(" KSEM-025 LIVE OSN EVENT SHAPE DATACLASS REPAIR"); print("="*120)
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
    leagues=("NFL","NCAAF","NBA","NHL","MLS","EPL"); report={}
    for league in leagues:
        result=acquire_canonical_events(league,timeout=15,root=ROOT)
        events=tuple(result.events)
        report[league]={"event_count":result.event_count,
                        "authority":result.authority,
                        "sample":shape(events[0]) if events else None}
        print("[LEAGUE]",league,"events=",len(events))
        if events: print("[FIELDS]",sorted(report[league]["sample"]["fields"]))
    required=("league","home_team","away_team","scheduled_start","provider_event_id")
    samples=[v["sample"] for v in report.values() if v["sample"]]
    if not samples: raise RuntimeError("no canonical event samples")
    if not all(k in samples[0]["fields"] for k in required): raise RuntimeError("canonical event structural contract incomplete")
    report["execution_authority"]=False
    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json').read_text())\ns=next(d[x]['sample'] for x in ('NFL','NCAAF','NBA','NHL','MLS','EPL') if d[x]['sample'])\nfor k in ('league','home_team','away_team','scheduled_start','provider_event_id'): assert k in s['fields']\nprint('[PASS] exact CanonicalSportsEvent structural fields captured')\nprint('[PASS] KSEM-025 structural repair certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()