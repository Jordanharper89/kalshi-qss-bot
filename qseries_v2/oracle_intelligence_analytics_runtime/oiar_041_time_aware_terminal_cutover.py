from pathlib import Path
from .oiar_027_trader_intent_classifier import classify_trader_intent
from .oiar_035_conversational_followup_resolution import classify_followup,followup_kind
from .oiar_036_trader_card_presentation_cutover import render_trader_cards
from .oiar_040_trader_opportunity_time_filter import read_time_filtered_trader_brief,requested_window
OIAR_041_BUILD_ID="OIAR-041";EXECUTION_AUTHORITY=False;_STATE={"rows":()}
def _render(root,query):
 rows=read_time_filtered_trader_brief(root,query,20);_STATE["rows"]=rows;want=requested_window(query)
 if want and not rows:return ("="*80,"ORACLE TRADER READ",f"Oracle has no snapshot-proven {want.lower()} markets in the current trader cohort.","It will not substitute UNKNOWN-time markets.","="*80)
 patched=[]
 for r in rows:
  x=dict(r);x["source_close_time"]=(r.get("time_relevance") or {}).get("event_time");patched.append(x)
 return render_trader_cards(tuple(patched),2)
def _follow(query):
 rows=_STATE.get("rows") or ()
 if not rows:return ("I do not have an active trader read to follow up on yet.",)
 t=rows[0].get("time_relevance") or {}
 if followup_kind(query)=="time":
  if not t.get("proven"):return ("Oracle cannot prove the market time from the current snapshot.","Time relevance: UNKNOWN")
  return (f"Time relevance: {t.get('label')}",f"Snapshot event time: {t.get('event_time')}")
 return None
def bind_time_aware_trader_terminal(base_module,root=None):
 if getattr(base_module,"_oiar041_bound",False):return base_module
 original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()
 def display_query(query,*,session=None,root=None,builder=None,write=print):
  canonical=base_module.normalize_query(query);use=Path(root or active).resolve()
  if classify_followup(canonical):
   lines=_follow(canonical)
   if lines:
    for line in lines:write(line)
    return None
  if classify_trader_intent(canonical).route=="trader_brief":
   for line in _render(use,canonical):write(line)
   return None
  kw={"session":session,"root":use,"write":write}
  if builder is not None:kw["builder"]=builder
  return original(canonical,**kw)
 base_module.display_query=display_query;base_module._oiar041_bound=True;return base_module
def physical_probe(root=None):
 lines=_render(Path(root or Path.cwd()).resolve(),"what are the plays for today?")
 return {"lines":len(lines),"today_filter_active":True,"execution_authority":False}
