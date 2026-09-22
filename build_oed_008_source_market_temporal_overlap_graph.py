from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_008_source_market_temporal_overlap_graph.py"; TEST=ROOT/"test_oed_008_source_market_temporal_overlap_graph.py"
assert (PKG/"oed_007_temporal_family_coactivity_graph.py").exists()
code=r"""
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
"""
MOD.write_text(code,encoding="utf-8")
test=r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_008_source_market_temporal_overlap_graph import build_graph
s=build_graph(Path.cwd())
assert s["market_bins"]>0 and s["source_bins"]>0 and s["edges"]
assert not s["source_is_independent_evidence_proven"] and not s["causality_claimed"] and not s["edge_proven"]
print("[MARKET_BINS]",s["market_bins"]); print("[SOURCE_BINS]",s["source_bins"]); print("[EDGES]",len(s["edges"]))
print("[TOP_OVERLAPS]")
for x in s["edges"][:30]: print(" ",x)
print("[PASS] source-market temporal overlap measured")
print("[PASS] overlap does not declare evidence independence or causality")
print("[PASS] OED-008 source-market temporal overlap graph certified")
"""
TEST.write_text(test,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-008 installer complete")
