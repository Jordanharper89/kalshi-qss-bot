
from __future__ import annotations
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_032_market_name_compression import compress_market_name
from .oiar_033_event_sport_context import classify_event_context
from .oiar_044_proven_current_day_trader_snapshot import STAGE as TODAY_STAGE
from .oiar_027_trader_intent_classifier import classify_trader_intent
from .oiar_035_conversational_followup_resolution import classify_followup,followup_kind

OIAR_046_BUILD_ID="OIAR-046"
OIAR_046_REVISION="OIAR_046_CURRENT_DAY_TERMINAL_CUTOVER_V1"
EXECUTION_AUTHORITY=False
_STATE={"rows":()}

def _read_today(root):
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TODAY_STAGE,))
            row=cur.fetchone()
        c.rollback()
    if not row: return {"markets":[],"market_count":0}
    p,h=row
    if isinstance(p,str): p=json.loads(p)
    if stable_hash(p)!=str(h): raise RuntimeError("OIAR-046 today snapshot hash mismatch")
    return p

def render_today(root,limit=2):
    p=_read_today(root);rows=tuple(p.get("markets",[]));_STATE["rows"]=rows
    if not rows:
        return ("="*80,"ORACLE TRADER READ","No snapshot-proven today markets are in the current trader cohort.","Oracle will not substitute UNKNOWN-time markets.","="*80)
    lines=["="*80,"ORACLE TRADER READ",f"{len(rows)} snapshot-proven today market(s) are in the current trader cohort.","-"*80]
    for i,m in enumerate(rows[:limit],1):
        ctx=classify_event_context(m);t=m.get("time_relevance") or {}
        lines += [f"#{i} {compress_market_name(m)}",f"   Market: {ctx['sport']} | Time: {t.get('label','UNKNOWN')}",f"   Read: {m.get('trader_takeaway') or 'NO EDGE RIGHT NOW'} | Direction: {m.get('direction') or 'NEUTRAL'}",f"   Why: {m.get('why') or 'Live evidence has not confirmed an edge.'}",f"   Risk: {m.get('risk') or 'UNKNOWN'}"]
    lines += ["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]
    return tuple(lines)

def bind_current_day_terminal(base_module,root=None):
    if getattr(base_module,"_oiar046_bound",False): return base_module
    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query);use=Path(root or active).resolve()
        if "today" in canonical and classify_trader_intent(canonical).route=="trader_brief":
            for line in render_today(use,2): write(line)
            return None
        if classify_followup(canonical) and followup_kind(canonical)=="time":
            rows=_STATE.get("rows") or ()
            if not rows:
                write("Oracle does not have an active snapshot-proven today market to confirm.")
                return None
            t=rows[0].get("time_relevance") or {}
            write(f"Time relevance: {t.get('label','UNKNOWN')}")
            write(f"Snapshot event time: {t.get('event_time')}")
            return None
        kw={"session":session,"root":use,"write":write}
        if builder is not None: kw["builder"]=builder
        return original(canonical,**kw)
    base_module.display_query=display_query;base_module._oiar046_bound=True
    return base_module

def physical_probe(root=None):
    lines=render_today(Path(root or Path.cwd()).resolve(),2)
    return {"lines":len(lines),"today_surface_active":True,"execution_authority":False}
