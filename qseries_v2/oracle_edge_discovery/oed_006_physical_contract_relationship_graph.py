
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
SCAN_ROWS=100000

def _ticker(obj):
    if not isinstance(obj,dict): return None
    p=obj.get("payload")
    if not isinstance(p,dict): return None
    m=p.get("message")
    if not isinstance(m,dict): return None
    t=m.get("market_ticker") or p.get("source_market_id")
    t=str(t or "")
    return t if t.startswith("KX") else None

def build_graph(root=None,scan_rows=SCAN_ROWS):
    root=Path(root or Path.cwd())
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute("SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT %s",(int(scan_rows),))
            rows=q.fetchall() or []
        c.rollback()
    nodes={}
    family_members=defaultdict(set)
    for seq,ts,sid,typ,obj in rows:
        if str(sid)!="source.kalshi.market_data": continue
        t=_ticker(obj)
        if not t: continue
        fam=t.split("-",1)[0]
        n=nodes.setdefault(t,{"ticker":t,"family":fam,"rows":0,"types":set(),"first_at":ts,"last_at":ts})
        n["rows"]+=1; n["types"].add(str(typ))
        if ts<n["first_at"]: n["first_at"]=ts
        if ts>n["last_at"]: n["last_at"]=ts
        family_members[fam].add(t)
    out_nodes=[]
    for n in nodes.values():
        n=dict(n); n["types"]=sorted(n["types"]); out_nodes.append(n)
    groups=[{"family":f,"contracts":len(v),"members":sorted(v)} for f,v in family_members.items()]
    groups.sort(key=lambda x:x["contracts"],reverse=True)
    return {"schema_version":"OED-006","scanned_rows":len(rows),"contract_nodes":out_nodes,"family_groups":groups,
            "relationship_basis":"PHYSICAL_TICKER_FAMILY_MEMBERSHIP_ONLY","semantic_equivalence_claimed":False,
            "edge_proven":False,"read_only":True}
