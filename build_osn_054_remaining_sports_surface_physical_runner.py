from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-054 REMAINING SPORTS SURFACE PHYSICAL RUNNER INSTALLER')
    print('='*118)
    require('test_osn_051_nhl_official_json_event_surface_physical_gate.py')
    require('test_osn_052_mls_official_stats_event_surface_physical_probe.py')
    require('test_osn_053_epl_official_json_event_surface_physical_gate.py')
    write('qseries_v2/oracle_source_network/certification/remaining_sports_surface_runner.py','\nimport subprocess,sys,json\nfrom pathlib import Path\n\nTESTS=(\n ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py","EXTRACTOR"),\n ("MLS","test_osn_052_mls_official_stats_event_surface_physical_probe.py","SURFACE_ONLY"),\n ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py","EXTRACTOR"),\n)\nREPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report.json")\n\ndef run():\n    rows=[]\n    for league,test,kind in TESTS:\n        try:\n            p=subprocess.run([sys.executable,test],text=True,capture_output=True,timeout=40)\n            ok=p.returncode==0\n            tail=(p.stdout+"\\n"+p.stderr)[-5000:]\n        except subprocess.TimeoutExpired:\n            ok=False;tail="TIMEOUT"\n        print(f"[SURFACE] {league} kind={kind} passed={ok}")\n        rows.append({"league":league,"kind":kind,"passed":ok,"tail":tail})\n    report={"passed":all(x["passed"] for x in rows),"rows":rows,"execution_authority":False}\n    REPORT.parent.mkdir(parents=True,exist_ok=True)\n    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")\n    return report\n')
    write('test_osn_054_remaining_sports_surface_physical_runner.py','\nfrom qseries_v2.oracle_source_network.certification.remaining_sports_surface_runner import run,REPORT\nr=run()\nprint("[REPORT]",{"passed":r["passed"],"rows":[(x["league"],x["kind"],x["passed"]) for x in r["rows"]],"execution_authority":r["execution_authority"]})\nassert all(x["passed"] for x in r["rows"]), "one or more remaining sports production surfaces failed physical certification"\nassert r["execution_authority"] is False\nassert REPORT.exists()\nprint("[PASS] OSN-054 remaining sports surface physical runner certified")\n')
    print('[PASS] bounded three-source physical runner installed')
    print('[PASS] durable evidence report enabled')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
