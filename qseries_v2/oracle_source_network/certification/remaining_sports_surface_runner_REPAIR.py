
import subprocess,sys,json
from pathlib import Path

TESTS=(
 ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py","EXTRACTOR"),
 ("MLS","test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py","EXTRACTOR"),
 ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py","EXTRACTOR"),
)

REPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report_REPAIR.json")

def run():
    rows=[]
    for league,test,kind in TESTS:
        try:
            p=subprocess.run([sys.executable,test],text=True,capture_output=True,timeout=40)
            ok=p.returncode==0
            text=(p.stdout+"\n"+p.stderr)
        except subprocess.TimeoutExpired:
            ok=False
            text="TIMEOUT"

        print(f"[SURFACE] {league} kind={kind} passed={ok}")
        if text:
            tail=text[-5000:]
            print(tail.rstrip())

        rows.append({
            "league":league,
            "kind":kind,
            "passed":ok,
            "test":test,
            "tail":text[-5000:],
        })

    report={
        "passed":all(x["passed"] for x in rows),
        "rows":rows,
        "execution_authority":False,
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
