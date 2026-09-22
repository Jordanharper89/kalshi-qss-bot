from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
READ_ONLY=True; EXECUTION_AUTHORITY=False
def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class MaturityView:
 pending:tuple; mature_now:tuple; total:int; execution_authority:bool=False
class MaturityRegistry:
 def __init__(self): self._items={}
 def add(self,predictions):
  for x in predictions: self._items.setdefault(x.prediction_id,x)
  return len(self._items)
 def view(self,now=None):
  now=now or datetime.now(timezone.utc); p=[]; m=[]
  for x in self._items.values():
   due=_dt(x.frozen_at)+timedelta(seconds=int(x.horizon_seconds))
   (m if now>=due else p).append(x)
  return MaturityView(tuple(p),tuple(m),len(self._items),False)
