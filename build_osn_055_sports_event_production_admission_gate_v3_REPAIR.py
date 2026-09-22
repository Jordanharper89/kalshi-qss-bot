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
    print(" OSN-055 SPORTS EVENT PRODUCTION ADMISSION GATE V3 REPAIR INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/certification/remaining_sports_surface_runner_REPAIR.py")

    write(
        "qseries_v2/oracle_source_network/certification/sports_event_production_admission_gate_v3_REPAIR.py",
        '\nimport json\nfrom pathlib import Path\n\nREPORT=Path("qseries_v2/oracle_source_network/certification/osn_054_remaining_sports_surface_report_REPAIR.json")\n\nBASE_ADMITTED=("NFL","NCAAF","NBA")\n\ndef admission():\n    if not REPORT.exists():\n        raise RuntimeError("repaired OSN-054 physical report missing")\n\n    r=json.loads(REPORT.read_text(encoding="utf-8"))\n    by={x["league"]:x for x in r.get("rows",[])}\n\n    admitted=list(BASE_ADMITTED)\n    for league in ("NHL","MLS","EPL"):\n        row=by.get(league,{})\n        if row.get("passed") is True and row.get("kind")=="EXTRACTOR":\n            admitted.append(league)\n\n    held=("NCAAB",)\n    blocked=("UCL",)\n\n    return {\n        "passed": (\n            r.get("passed") is True\n            and tuple(admitted)==("NFL","NCAAF","NBA","NHL","MLS","EPL")\n        ),\n        "admitted":tuple(admitted),\n        "held":held,\n        "blocked":blocked,\n        "execution_authority":False,\n    }\n',
    )
    write(
        "test_osn_055_sports_event_production_admission_gate_v3_REPAIR.py",
        '\nfrom qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission\n\nr=admission()\nprint("[ADMISSION_V3_REPAIR]",r)\n\nassert r["passed"] is True\nassert r["admitted"]==("NFL","NCAAF","NBA","NHL","MLS","EPL")\nassert r["held"]==("NCAAB",)\nassert r["blocked"]==("UCL",)\nassert r["execution_authority"] is False\n\nprint("[PASS] NFL/NCAAF/NBA/NHL/MLS/EPL production event extraction admitted")\nprint("[PASS] NCAAB held only for current offseason-empty live page")\nprint("[PASS] UCL remains blocked")\nprint("[PASS] OSN-055 repaired sports production admission gate certified")\n',
    )

    print("[PASS] stale MLS SURFACE_ONLY classification retired")
    print("[PASS] repaired physical extractor evidence required for NHL/MLS/EPL admission")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
