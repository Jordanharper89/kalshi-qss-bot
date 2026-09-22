
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
SCAN_ROWS=100000; BIN_SECONDS=60

def _ticker(obj):
    if not isinstance(obj,dict): return None
    p=obj.get("payload")
    if not isinstance(p,dict): return None
    m=p.get("message")
    if not isinstance(m,dict): return None
    t=str(m.get("market_ticker") or p.get("source_market_id") or "")
    return t if t.startswith("KX") else None

def build_graph(root=None):
    root=Path(root or Path.cwd())
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute("SELECT observed_at,source_id,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT %s",(SCAN_ROWS,))
            rows=q.fetchall() or []
        c.rollback()
    bins=defaultdict(set); fam_bins=Counter()
    for ts,sid,obj in rows:
        if str(sid)!="source.kalshi.market_data": continue
        t=_ticker(obj)
        if not t: continue
        fam=t.split("-",1)[0]
        epoch=int(ts.timestamp()); b=epoch-(epoch%BIN_SECONDS)
        bins[b].add(fam); fam_bins[fam]+=1
    pairs=Counter()
    for fs in bins.values():
        a=sorted(fs)
        for i in range(len(a)):
            for j in range(i+1,len(a)): pairs[(a[i],a[j])]+=1
    edges=[{"family_a":a,"family_b":b,"shared_minute_bins":n} for (a,b),n in pairs.items()]
    edges.sort(key=lambda x:x["shared_minute_bins"],reverse=True)
    return {"schema_version":"OED-007","minute_bins":len(bins),"families":len(fam_bins),"edges":edges,
            "relationship_basis":"TEMPORAL_COACTIVITY_ONLY","causality_claimed":False,"edge_proven":False,"read_only":True}
