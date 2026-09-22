from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status
from qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page
from qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget
OPC_045_BUILD_ID="OPC-045";OPC_045_REVISION="OPC_045_EXACT_OIAR003_INDEXED_REBUILD"
def physical_probe(root=None,max_markets=100,timeout_ms=15000):
 root=Path(root or Path.cwd()).resolve();st=_index_status(root)
 if not all(st):raise RuntimeError("OIAR-003 index not valid/ready/live")
 b=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0);_,markets,_,raw=fetch_rotating_open_page(root,b);ids=tuple(dict.fromkeys(str(x.get("ticker") or "") for x in markets if x.get("ticker")))[:max_markets]
 sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at FROM unnest(%s::text[]) AS wanted(market_id) LEFT JOIN LATERAL (SELECT sequence_number,observed_at FROM public.oracle_canonical_observations WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=wanted.market_id ORDER BY sequence_number DESC LIMIT 3) h ON TRUE ORDER BY wanted.market_id,h.sequence_number DESC"""
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'");cur.execute("EXPLAIN (FORMAT JSON) "+sql,(list(ids),));plan=cur.fetchone()[0];cur.execute(sql,(list(ids),));rows=cur.fetchall() or []
  c.rollback()
 grouped={t:[] for t in ids}
 for t,seq,obs in rows:
  if seq is not None:grouped[str(t)].append((seq,obs))
 repeated=sum(len(v)>=2 for v in grouped.values());observed=sum(bool(v) for v in grouped.values());pt=str(plan)
 if INDEX_NAME not in pt:raise RuntimeError("OPC-045 exact lookup did not use OIAR-003 index")
 return {"raw_page_markets":raw,"checked":len(ids),"markets_with_snapshot":observed,"markets_with_repeated_snapshots":repeated,"plan_uses_index":True,"index_name":INDEX_NAME,"sample":[(k,len(v)) for k,v in list(grouped.items())[:20]],"read_only":True,"execution_authority":False}
def verify_opc_045():return OPC_045_BUILD_ID=="OPC-045"
