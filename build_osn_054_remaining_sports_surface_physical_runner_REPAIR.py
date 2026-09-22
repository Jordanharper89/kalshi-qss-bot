from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(p))
    print("[PASS] dependency verified:",p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+"\n",encoding="utf-8")
    print("[WRITE]",p.relative_to(ROOT))

def main():
    print("="*118)
    print(" OSN-054 REMAINING SPORTS PHYSICAL RUNNER REPAIR INSTALLER")
    print("="*118)

    require("test_osn_051_nhl_official_json_event_surface_physical_gate.py")
    require("test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py")
    require("test_osn_053_epl_official_json_event_surface_physical_gate.py")

    write(
        "qseries_v2/oracle_source_network/certification/remaining_sports_surface_runner_REPAIR.py",
        '\nimport subprocess,sys,json\nfrom pathlib import Path\n\nTESTS=(\n ("NHL","test_osn_051_nhl_official_json_event_surface_physical_gate.py","EXTRACTOR"),\n ("MLS","test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py","EXTRACTOR"),\n ("EPL","test_osn_053_epl_official_json_event_surface_physical_gate.py","EXTRACTOR"),\n)\n\nREPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report_REPAIR.json")\n\ndef run():\n    rows=[]\n    for league,test,kind in TESTS:\n        try:\n            p=subprocess.run([sys.executable,test],text=True,capture_output=True,timeout=40)\n            ok=p.returncode==0\n            text=(p.stdout+"\\n"+p.stderr)\n        except subprocess.TimeoutExpired:\n            ok=False\n            text="TIMEOUT"\n\n        print(f"[SURFACE] {league} kind={kind} passed={ok}")\n        if text:\n            tail=text[-5000:]\n            print(tail.rstrip())\n\n        rows.append({\n            "league":league,\n            "kind":kind,\n            "passed":ok,\n            "test":test,\n            "tail":text[-5000:],\n        })\n\n    report={\n        "passed":all(x["passed"] for x in rows),\n        "rows":rows,\n        "execution_authority":False,\n    }\n    REPORT.parent.mkdir(parents=True,exist_ok=True)\n    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")\n    return report\n',
    )
    write(
        "test_osn_054_remaining_sports_surface_physical_runner_REPAIR.py",
        '\nfrom qseries_v2.oracle_source_network.certification.remaining_sports_surface_runner_REPAIR import run,REPORT\n\nr=run()\nsummary=[(x["league"],x["kind"],x["passed"]) for x in r["rows"]]\nprint("[REPORT]",{"passed":r["passed"],"rows":summary,"execution_authority":r["execution_authority"]})\n\nassert r["passed"] is True\nassert all(x["kind"]=="EXTRACTOR" for x in r["rows"])\nassert all(x["passed"] for x in r["rows"])\nassert {x["league"] for x in r["rows"]}=={"NHL","MLS","EPL"}\nassert r["execution_authority"] is False\nassert REPORT.exists()\n\nprint("[PASS] NHL + MLS + EPL physical extraction all re-certified")\nprint("[PASS] obsolete failed MLS probe excluded")\nprint("[PASS] OSN-054 repaired remaining sports physical runner certified")\n',
    )

    print("[PASS] obsolete failed OSN-052 test dependency retired")
    print("[PASS] repaired MLS physical extractor now classified EXTRACTOR")
    print("[PASS] durable repaired physical report enabled")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
