from dataclasses import dataclass
@dataclass(frozen=True)
class RehydratedStateHead: subject_id:str; version:int; state_hash:str; version_hash:str
def rehydrate_state_heads(rows):
 d={}
 for s,v,h,vh in rows:
  if s not in d or int(v)>d[s].version:d[s]=RehydratedStateHead(str(s),int(v),str(h),str(vh))
 return tuple(d[k] for k in sorted(d))
def load_state_heads(c):
 cur=c.cursor()
 try: cur.execute("SELECT subject_id, version, state_hash, version_hash FROM oracle_intelligence_state_versions ORDER BY subject_id ASC, version DESC"); return rehydrate_state_heads(cur.fetchall())
 finally:
  if hasattr(cur,"close"):cur.close()
def verify_ois_013_startup_recovery_state_rehydration(): return rehydrate_state_heads((("x",1,"a","b"),("x",2,"c","d")))[0].version==2
