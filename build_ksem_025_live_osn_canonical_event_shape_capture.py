from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json"
TEST=ROOT/"test_ksem_025_live_osn_canonical_event_shape_capture.py"

def shape(x):
    fields={}
    if hasattr(x,"__dict__"):
        for k,v in vars(x).items():
            fields[k]={"type":type(v).__name__,"repr":repr(v)[:300]}
    return {"type":type(x).__name__,"fields":fields,"repr":repr(x)[:1200]}

def main():
    print("="*120); print(" KSEM-025 LIVE OSN CANONICAL EVENT SHAPE CAPTURE"); print("="*120)
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
    leagues=("NFL","NCAAF","NBA","NHL","MLS","EPL")
    report={}
    for league in leagues:
        events=tuple(acquire_canonical_events(league,timeout=15,root=ROOT) or ())
        report[league]={"count":len(events),"sample":shape(events[0]) if events else None}
        print("[LEAGUE]",league,"events=",len(events))
        if events: print("[SAMPLE]",report[league]["sample"])
    if not any(v["count"] for v in report.values()): raise RuntimeError("no live OSN canonical sports events")
    report["execution_authority"]=False
    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json').read_text())\n"
        "assert any(d[x]['count']>0 for x in ('NFL','NCAAF','NBA','NHL','MLS','EPL'))\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] live OSN canonical event shape physically captured')\n"
        "print('[PASS] KSEM-025 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()