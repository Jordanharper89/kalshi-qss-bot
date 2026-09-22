from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-059 UNIVERSAL SPORTS EVENT PHYSICAL RUNNER INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/certification/sports_event_production_admission_gate_v3_REPAIR.py')
    put('qseries_v2/oracle_source_network/certification/universal_sports_event_runner.py','\nimport subprocess,sys,json\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission\n\nPHYSICAL_TESTS=(\n ("NFL","test_osn_044_nfl_exact_live_escaped_state_event_extractor_REPAIR.py"),\n ("NCAAF","test_osn_045_ncaaf_exact_scoreboard_event_extractor_REPAIR.py"),\n ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py"),\n ("MLS","test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py"),\n ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py"),\n)\nREPORT=Path("qseries_v2/oracle_source_network/certification/osn_059_universal_sports_event_report.json")\n\ndef run():\n    rows=[]\n    for league,test in PHYSICAL_TESTS:\n        if not Path(test).exists():\n            rows.append({"league":league,"passed":False,"reason":"exact_test_missing"})\n            print(f"[UNIVERSAL] {league} passed=False reason=exact_test_missing")\n            continue\n        try:\n            r=subprocess.run([sys.executable,test],capture_output=True,text=True,timeout=45)\n            ok=r.returncode==0\n            tail=(r.stdout+"\\n"+r.stderr)[-3500:]\n        except subprocess.TimeoutExpired:\n            ok=False;tail="TIMEOUT"\n        rows.append({"league":league,"passed":ok,"tail":tail})\n        print(f"[UNIVERSAL] {league} passed={ok}")\n\n    a=admission()\n    nba_certified=("NBA" in a.get("admitted",()) and a.get("passed") is True)\n    print(f"[UNIVERSAL] NBA inherited_certified_admission={nba_certified}")\n\n    report={\n        "passed":all(x["passed"] for x in rows) and nba_certified,\n        "physical_reruns":rows,\n        "nba_certified_admission":nba_certified,\n        "execution_authority":False,\n    }\n    REPORT.parent.mkdir(parents=True,exist_ok=True)\n    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")\n    return report\n')
    put('test_osn_059_universal_sports_event_physical_runner.py','\nfrom qseries_v2.oracle_source_network.certification.universal_sports_event_runner import run,REPORT\nr=run()\nprint("[UNIVERSAL_REPORT]",{\n    "physical_reruns":[(x["league"],x["passed"]) for x in r["physical_reruns"]],\n    "nba_certified_admission":r["nba_certified_admission"],\n    "passed":r["passed"],\n})\nassert r["passed"] is True\nassert len(r["physical_reruns"])==5\nassert all(x["passed"] for x in r["physical_reruns"])\nassert r["nba_certified_admission"] is True\nassert r["execution_authority"] is False\nassert REPORT.exists()\nprint("[PASS] five exact physical source tests re-run + NBA certified admission retained")\nprint("[PASS] OSN-059 universal sports event runner certified")\n')
    print('[PASS] only exact known physical test filenames are rerun')
    print('[PASS] NBA retained from certified OSN-055 admission rather than guessed test filename')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
