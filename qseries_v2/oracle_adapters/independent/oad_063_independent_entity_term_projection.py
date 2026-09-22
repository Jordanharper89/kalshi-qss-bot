from dataclasses import dataclass
import re
READ_ONLY=True
EXECUTION_AUTHORITY=False
STOP={"the","and","for","with","from","this","that","will","are","was","were","has","have","into","about","active"}
@dataclass(frozen=True,slots=True)
class EntityTerms: observation_id:str; terms:tuple
def extract_independent_entity_terms(x,limit=24):
 p=dict(x.payload); words=re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}",(str(p.get("subject",""))+" "+str(p.get("source_payload",""))).lower())
 out=[]; seen=set()
 for w in words:
  if w in STOP or w in seen: continue
  seen.add(w); out.append(w)
  if len(out)>=limit: break
 return EntityTerms(x.observation_id,tuple(out))
