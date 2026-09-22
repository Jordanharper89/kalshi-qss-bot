
from datetime import datetime,timezone,timedelta
from collections import Counter
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import _backend
PREFIX="source.dex.solana.token_pools."
def discover(root=None,days=30,window_minutes=30,limit=10000):
 backend=_backend(root);end=datetime.now(timezone.utc);start=end-timedelta(days=int(days));windows=0
 found=Counter();samples=[];cursor=start
 while cursor<end:
  stop=min(cursor+timedelta(minutes=int(window_minutes)),end);requested=datetime.now(timezone.utc)
  req=CanonicalPersistenceQueryRequest.by_observed_time_range(
   query_id=f"query.ssi002k.{windows}",backend_id=backend.backend_id,observed_from=cursor,observed_to=stop,
   limit=int(limit),requested_at=requested,query_metadata={"read_only":True,"purpose":"ssi002k_window_source_discovery"})
  rows=tuple(backend.query(request=req));pool=tuple(r for r in rows if str(r.source_id).startswith(PREFIX))
  for r in pool:found[str(r.source_id)[len(PREFIX):]]+=1
  if pool:samples.extend((str(r.observation_id),str(r.source_id),str(r.observed_at)) for r in pool[:10])
  print("[WINDOW]",windows,cursor.isoformat(),stop.isoformat(),"rows=",len(rows),"pool_rows=",len(pool))
  windows+=1
  if found:break
  cursor=stop
 ranked=tuple(sorted(found.items(),key=lambda x:(-x[1],x[0])))
 r={"windows_scanned":windows,"ranked_tokens":ranked,"samples":tuple(samples[:20]),"read_only":True,"execution_authority":False}
 print("[DISCOVERY]",r)
 if not ranked:raise AssertionError("no persisted token-pool source found in bounded ascending time windows")
 return r
