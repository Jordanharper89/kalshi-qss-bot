from dataclasses import dataclass
from datetime import datetime
READ_ONLY=True;EXECUTION_AUTHORITY=False
def _dt(v):return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class TemporalReadiness:
 token_address:str;records:int;span_seconds:float;ready:bool;state:str;execution_authority:bool=False
def temporal_readiness(token_address,records,min_records=2,min_span_seconds=60.0):
 rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at)))
 span=0.0 if len(rows)<2 else (_dt(rows[-1].observed_at)-_dt(rows[0].observed_at)).total_seconds()
 ok=len(rows)>=int(min_records) and span>=float(min_span_seconds)
 return TemporalReadiness(token_address,len(rows),span,ok,"READY_60S" if ok else "WARMING",False)
