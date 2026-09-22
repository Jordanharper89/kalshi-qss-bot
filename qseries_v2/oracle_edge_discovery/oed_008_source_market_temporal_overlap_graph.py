
from pathlib import Path
from collections import defaultdict,Counter
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
SCAN_ROWS=250000; BIN_SECONDS=60

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
    market_bins=defaultdict(set); source_bins=defaultdict(set)
    for ts,sid,obj in rows:
        b=int(ts.timestamp()); b-=b%BIN_SECONDS; sid=str(sid)
        if sid=="source.kalshi.market_data":
            t=_ticker(obj)
            if t: market_bins[b].add(t.split("-",1)[0])
        elif not sid.startswith("source.polymarket."):
            source_bins[b].add(sid)
    pairs=Counter()
    for b,fams in market_bins.items():
        for fam in fams:
            for sid in source_bins.get(b,()): pairs[(fam,sid)]+=1
    edges=[{"family":f,"source_id":s,"shared_minute_bins":n} for (f,s),n in pairs.items()]
    edges.sort(key=lambda x:x["shared_minute_bins"],reverse=True)
    return {"schema_version":"OED-008","edges":edges,"market_bins":len(market_bins),"source_bins":len(source_bins),
            "relationship_basis":"TEMPORAL_OVERLAP_ONLY","source_is_independent_evidence_proven":False,
            "causality_claimed":False,"edge_proven":False,"read_only":True}
