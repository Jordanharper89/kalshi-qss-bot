
import subprocess,sys,json
from pathlib import Path

TESTS=(
 ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py","EXTRACTOR"),
 ("MLS","test_osn_052_mls_official_stats_event_surface_physical_probe.py","SURFACE_ONLY"),
 ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py","EXTRACTOR"),
)
REPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report.json")

def run():
    rows=[]
    for league,test,kind in TESTS:
        try:
            p=subprocess.run([sys.executable,test],text=True,capture_output=True,timeout=40)
            ok=p.returncode==0
            tail=(p.stdout+"\n"+p.stderr)[-5000:]
        except subprocess.TimeoutExpired:
            ok=False;tail="TIMEOUT"
        print(f"[SURFACE] {league} kind={kind} passed={ok}")
        rows.append({"league":league,"kind":kind,"passed":ok,"tail":tail})
    report={"passed":all(x["passed"] for x in rows),"rows":rows,"execution_authority":False}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
