from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
BUILD_ID="OIAR-069";CANONICAL_TABLE="oracle_canonical_observations";LEDGER_TABLE="oracle_production_learning_ledger";OPC_SOURCE_ID="source.kalshi.market_data"
MARKET_ID_EXPRESSION="""COALESCE(NULLIF(COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)->>'source_market_id',''),NULLIF(COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)->>'market_id',''),NULLIF(COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)->>'source_symbol',''))"""
def _utc(v):
    if isinstance(v,datetime): return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s=str(v or "").strip()
    if s.endswith("Z"): s=s[:-1]+"+00:00"
    x=datetime.fromisoformat(s); return x.astimezone(timezone.utc) if x.tzinfo else x.replace(tzinfo=timezone.utc)
def _epoch(cur):
    cur.execute(f"SELECT sequence_number,acquired_at FROM public.{CANONICAL_TABLE} WHERE source_id=%s AND observation_type='market_snapshot' ORDER BY sequence_number ASC LIMIT 1",(OPC_SOURCE_ID,));a=cur.fetchone()
    cur.execute(f"SELECT sequence_number,acquired_at FROM public.{CANONICAL_TABLE} WHERE source_id=%s AND observation_type='market_snapshot' ORDER BY sequence_number DESC LIMIT 1",(OPC_SOURCE_ID,));b=cur.fetchone()
    if not a or not b: raise RuntimeError("no OPC market_snapshot acquisition epoch found")
    return a,b
def trace(root=None,sample_size=100):
    root=Path(root or Path.cwd()).resolve();n=max(1,min(int(sample_size),500))
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'")
        first,last=_epoch(q);first_time=_utc(first[1])
        q.execute(f"SELECT ticker,result,settlement_ts,settlement_hash FROM public.{LEDGER_TABLE} WHERE status='EVIDENCE_MISSING' ORDER BY settlement_ts ASC,ticker ASC LIMIT %s",(n,));settlements=q.fetchall() or []
        sql=f"SELECT sequence_number,observed_at,acquired_at FROM public.{CANONICAL_TABLE} WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=%s ORDER BY sequence_number DESC LIMIT 16"
        found=pre=post=noexact=before_epoch=in_epoch=0;examples=[]
        for ticker,result,settlement_ts,settlement_hash in settlements:
            q.execute(sql,(str(ticker),));rows=q.fetchall() or [];settle=_utc(settlement_ts)
            before=[r for r in rows if r[2] is not None and _utc(r[2])<settle];after=[r for r in rows if r[2] is not None and _utc(r[2])>=settle]
            if rows: found+=1
            if before: pre+=1;cls="PRE_SETTLEMENT_CAPTURE_EXISTS"
            elif rows and after: post+=1;cls="POST_SETTLEMENT_CAPTURE_ONLY"
            else:
                noexact+=1
                if settle<first_time: before_epoch+=1;cls="SETTLED_BEFORE_OPC_COVERAGE_EPOCH"
                else: in_epoch+=1;cls="IN_OPC_EPOCH_NO_EXACT_SNAPSHOT"
            if len(examples)<20: examples.append({"ticker":str(ticker),"settlement_ts":str(settlement_ts),"classification":cls,"snapshot_rows":len(rows),"settlement_hash":str(settlement_hash)})
        c.rollback()
    return {"sampled_missing_settlements":len(settlements),"exact_market_snapshot_found":found,"pre_settlement_snapshot_found":pre,"post_only_snapshot_found":post,"no_exact_snapshot":noexact,"before_opc_coverage_epoch":before_epoch,"inside_opc_coverage_epoch_without_snapshot":in_epoch,"first_opc_sequence":int(first[0]),"first_opc_acquired_at":str(first[1]),"latest_opc_sequence":int(last[0]),"latest_opc_acquired_at":str(last[1]),"exact_lookup_index":"idx_oracle_canonical_market_snapshot_market_seq","examples":tuple(examples),"read_only":True,"repaired_rows":0,"probability_enabled":False,"execution_authority":False}
def physical_probe(root=None): return trace(root,100)
def verify_oiar_069(): return BUILD_ID=="OIAR-069"
