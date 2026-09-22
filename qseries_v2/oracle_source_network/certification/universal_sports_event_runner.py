
import subprocess,sys,json
from pathlib import Path
from qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission

PHYSICAL_TESTS=(
 ("NFL","test_osn_044_nfl_exact_live_escaped_state_event_extractor_REPAIR.py"),
 ("NCAAF","test_osn_045_ncaaf_exact_scoreboard_event_extractor_REPAIR.py"),
 ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py"),
 ("MLS","test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py"),
 ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py"),
)
REPORT=Path("qseries_v2/oracle_source_network/certification/osn_059_universal_sports_event_report.json")

def run():
    rows=[]
    for league,test in PHYSICAL_TESTS:
        if not Path(test).exists():
            rows.append({"league":league,"passed":False,"reason":"exact_test_missing"})
            print(f"[UNIVERSAL] {league} passed=False reason=exact_test_missing")
            continue
        try:
            r=subprocess.run([sys.executable,test],capture_output=True,text=True,timeout=45)
            ok=r.returncode==0
            tail=(r.stdout+"\n"+r.stderr)[-3500:]
        except subprocess.TimeoutExpired:
            ok=False;tail="TIMEOUT"
        rows.append({"league":league,"passed":ok,"tail":tail})
        print(f"[UNIVERSAL] {league} passed={ok}")

    a=admission()
    nba_certified=("NBA" in a.get("admitted",()) and a.get("passed") is True)
    print(f"[UNIVERSAL] NBA inherited_certified_admission={nba_certified}")

    report={
        "passed":all(x["passed"] for x in rows) and nba_certified,
        "physical_reruns":rows,
        "nba_certified_admission":nba_certified,
        "execution_authority":False,
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
