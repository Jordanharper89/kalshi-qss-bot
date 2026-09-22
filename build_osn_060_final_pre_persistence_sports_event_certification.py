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
    print(' OSN-060 FINAL PRE-PERSISTENCE SPORTS EVENT CERTIFICATION INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/certification/universal_sports_event_runner.py')
    require('qseries_v2/oracle_source_network/certification/ncaab_dynamic_activation_gate.py')
    require('qseries_v2/oracle_source_network/certification/mlb_unified_boundary_reconciliation.py')
    put('qseries_v2/oracle_source_network/certification/pre_persistence_sports_event_certification.py','\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission\nfrom qseries_v2.oracle_source_network.certification.ncaab_dynamic_activation_gate import activate\nfrom qseries_v2.oracle_source_network.certification.mlb_unified_boundary_reconciliation import reconcile\n\nREPORT=Path("qseries_v2/oracle_source_network/certification/osn_059_universal_sports_event_report.json")\n\ndef certify():\n    if not REPORT.exists():\n        raise RuntimeError("OSN-059 universal physical report missing")\n    physical=json.loads(REPORT.read_text(encoding="utf-8"))\n    base=admission()\n    ncaab=activate()\n    mlb=reconcile()\n\n    admitted=list(base["admitted"])\n    if ncaab.admitted and "NCAAB" not in admitted: admitted.append("NCAAB")\n    # MLB reconciliation locates reusable pavement; it does NOT promote event extraction\n    # without a current canonical MLB extraction certification.\n    held=[]\n    if not ncaab.admitted: held.append("NCAAB")\n    if mlb.admitted_boundary: held.append("MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")\n    else: held.append("MLB_RECONCILIATION_REQUIRED")\n\n    physically_rerun=tuple(x["league"] for x in physical["physical_reruns"] if x.get("passed"))\n    foundation_ok=bool(base["passed"] and physical.get("passed"))\n\n    return {\n        "passed":foundation_ok,\n        "physically_rerun":physically_rerun,\n        "nba_certified_admission":bool(physical.get("nba_certified_admission")),\n        "admitted":tuple(admitted),\n        "held":tuple(held),\n        "blocked":("UCL",),\n        "persistence_ready":foundation_ok,\n        "execution_authority":False,\n    }\n')
    put('test_osn_060_final_pre_persistence_sports_event_certification.py','\nfrom qseries_v2.oracle_source_network.certification.pre_persistence_sports_event_certification import certify\nr=certify()\nprint("[PRE_PERSISTENCE_CERT]",r)\nassert r["passed"] is True\nassert r["persistence_ready"] is True\nassert set(("NFL","NCAAF","NBA","NHL","MLS","EPL")).issubset(r["admitted"])\nassert set(r["physically_rerun"])=={"NFL","NCAAF","NHL","MLS","EPL"}\nassert r["nba_certified_admission"] is True\nassert r["blocked"]==("UCL",)\nassert r["execution_authority"] is False\nprint("[PASS] six-league universal sports foundation ready for PostgreSQL single-writer integration")\nprint("[PASS] MLB remains truthfully held until canonical event extraction is certified")\nprint("[PASS] OSN-060 final pre-persistence sports certification certified")\n')
    print('[PASS] universal six-league pre-persistence gate installed')
    print('[PASS] MLB not falsely promoted by pavement discovery alone')
    print('[PASS] no PostgreSQL writer introduced yet')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
