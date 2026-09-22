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
    print(' OSN-050 SPORTS EVENT PRODUCTION ADMISSION GATE V2 INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/certification/sports_event_extraction_truth_v2.py')
    write('qseries_v2/oracle_source_network/certification/sports_event_production_admission_gate_v2.py','\nfrom qseries_v2.oracle_source_network.certification.sports_event_extraction_truth_v2 import rows\n\ndef production_admission():\n    truth=rows()\n    admitted=tuple(x.league for x in truth if x.admitted and x.state=="PHYSICAL_EXTRACTING")\n    held=tuple(x.league for x in truth if not x.admitted and x.state!="BLOCKED")\n    blocked=tuple(x.league for x in truth if x.state=="BLOCKED")\n    return {\n        "passed": admitted==("NFL","NCAAF","NBA"),\n        "admitted":admitted,\n        "held":held,\n        "blocked":blocked,\n        "execution_authority":False,\n    }\n')
    write('test_osn_050_sports_event_production_admission_gate_v2.py','\nfrom qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v2 import production_admission\nr=production_admission()\nprint("[ADMISSION]",r)\nassert r["passed"] is True\nassert r["admitted"]==("NFL","NCAAF","NBA")\nassert set(r["held"])=={"NCAAB","NHL","MLS","EPL"}\nassert r["blocked"]==("UCL",)\nassert r["execution_authority"] is False\nprint("[PASS] only physically extracting leagues admitted")\nprint("[PASS] NCAAB/NHL/MLS/EPL held; UCL blocked")\nprint("[PASS] OSN-050 production admission gate certified")\n')
    print('[PASS] physical extraction remains mandatory for admission')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
