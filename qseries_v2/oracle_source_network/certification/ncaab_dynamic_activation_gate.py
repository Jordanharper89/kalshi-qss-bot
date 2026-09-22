
import subprocess,sys,re
from dataclasses import dataclass
from pathlib import Path

TEST=Path("test_osn_046_ncaab_exact_scoreboard_event_extractor.py")
ALT=Path("test_osn_046_ncaab_exact_scoreboard_event_extractor_REPAIR.py")

@dataclass(frozen=True)
class NCAABActivation:
    status:str
    events:int
    admitted:bool
    source_test:str
    execution_authority:bool=False

def activate():
    test=TEST if TEST.exists() else ALT if ALT.exists() else None
    if test is None:
        return NCAABActivation("CERTIFIED_TEST_NOT_FOUND",0,False,"")
    try:
        p=subprocess.run([sys.executable,str(test)],capture_output=True,text=True,timeout=35)
    except subprocess.TimeoutExpired:
        return NCAABActivation("PHYSICAL_TEST_TIMEOUT",0,False,str(test))
    text=p.stdout+"\n"+p.stderr
    if p.returncode!=0:
        return NCAABActivation("PHYSICAL_TEST_FAILED",0,False,str(test))
    m=re.search(r"events=(\d+)",text)
    n=int(m.group(1)) if m else 0
    if n>0:
        return NCAABActivation("PHYSICAL_EXTRACTING",n,True,str(test))
    return NCAABActivation("EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",0,False,str(test))
