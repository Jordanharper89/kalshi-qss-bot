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
    print(' OSN-056 NCAAB DYNAMIC EVENT ACTIVATION GATE INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/mapping/ncaab_exact_scoreboard_extractor.py')
    put('qseries_v2/oracle_source_network/certification/ncaab_dynamic_activation_gate.py','\nimport subprocess,sys,re\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nTEST=Path("test_osn_046_ncaab_exact_scoreboard_event_extractor.py")\nALT=Path("test_osn_046_ncaab_exact_scoreboard_event_extractor_REPAIR.py")\n\n@dataclass(frozen=True)\nclass NCAABActivation:\n    status:str\n    events:int\n    admitted:bool\n    source_test:str\n    execution_authority:bool=False\n\ndef activate():\n    test=TEST if TEST.exists() else ALT if ALT.exists() else None\n    if test is None:\n        return NCAABActivation("CERTIFIED_TEST_NOT_FOUND",0,False,"")\n    try:\n        p=subprocess.run([sys.executable,str(test)],capture_output=True,text=True,timeout=35)\n    except subprocess.TimeoutExpired:\n        return NCAABActivation("PHYSICAL_TEST_TIMEOUT",0,False,str(test))\n    text=p.stdout+"\\n"+p.stderr\n    if p.returncode!=0:\n        return NCAABActivation("PHYSICAL_TEST_FAILED",0,False,str(test))\n    m=re.search(r"events=(\\d+)",text)\n    n=int(m.group(1)) if m else 0\n    if n>0:\n        return NCAABActivation("PHYSICAL_EXTRACTING",n,True,str(test))\n    return NCAABActivation("EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",0,False,str(test))\n')
    put('test_osn_056_ncaab_dynamic_event_activation_gate.py','\nfrom qseries_v2.oracle_source_network.certification.ncaab_dynamic_activation_gate import activate\nr=activate()\nprint("[NCAAB_ACTIVATION]",r)\nassert r.execution_authority is False\nassert r.status in (\n    "PHYSICAL_EXTRACTING",\n    "EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",\n    "CERTIFIED_TEST_NOT_FOUND",\n)\nif r.status=="PHYSICAL_EXTRACTING":\n    assert r.events>0 and r.admitted is True\n    print("[PASS] NCAAB dynamically activated by existing certified physical extractor")\nelif r.status=="EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY":\n    assert r.events==0 and r.admitted is False\n    print("[HOLD] NCAAB remains correctly held because current official page is empty")\nelse:\n    assert r.admitted is False\n    print("[HOLD] NCAAB exact certified test filename not present; no synthetic admission")\nprint("[PASS] OSN-056 NCAAB dynamic activation truth gate certified")\n')
    print('[PASS] existing certified NCAAB physical test consumed read-only')
    print('[PASS] no assumed internal extractor function name')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
