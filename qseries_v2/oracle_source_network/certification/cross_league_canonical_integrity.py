
from dataclasses import dataclass

REQUIRED=("league","season","provider","home_team","away_team","scheduled_start","source_observed_at","source_authority")

@dataclass(frozen=True)
class IntegrityResult:
    passed:bool
    checked:int
    failures:tuple
    execution_authority:bool=False

def validate(events):
    failures=[]
    seen=set()
    for i,e in enumerate(events):
        for field in REQUIRED:
            if not getattr(e,field,None):
                failures.append((i,"missing",field))
        cid=getattr(e,"canonical_event_id",None)
        if not cid:
            failures.append((i,"missing","canonical_event_id"))
        elif cid in seen:
            failures.append((i,"duplicate","canonical_event_id"))
        else:
            seen.add(cid)
        if getattr(e,"execution_authority",None) is not False:
            failures.append((i,"invalid","execution_authority"))
        if getattr(e,"read_only",None) is not True:
            failures.append((i,"invalid","read_only"))
    return IntegrityResult(not failures,len(tuple(events)),tuple(failures))
