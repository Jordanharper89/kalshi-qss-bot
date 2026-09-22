from dataclasses import dataclass
from datetime import datetime,timezone
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class HotToken:
 token_address:str;first_seen:str;last_seen:str;discoveries:int;state:str="HOT";execution_authority:bool=False
class HotTokenRegistry:
 def __init__(self):self._x={}
 def refresh(self,tokens,now=None):
  now=(now or datetime.now(timezone.utc)).isoformat()
  for t in tokens:
   old=self._x.get(t)
   self._x[t]=HotToken(t,old.first_seen if old else now,now,(old.discoveries+1) if old else 1,"HOT",False)
  return tuple(self._x.values())
 def tokens(self):return tuple(self._x)
