from .oiar_012_trader_interpretation_model import interpret_trader_row
OIAR_013_BUILD_ID="OIAR-013"
def render_trader_brief(rows,freshness_status=None,age_seconds=None,limit=5):
 z=["="*80,"ORACLE TRADER BRIEF","READ-ONLY | TRADER INTERPRETATION, NOT EXECUTION","-"*80]
 if freshness_status:z+=["Data: %s | snapshot age: %.0fs"%(freshness_status,float(age_seconds or 0)),"-"*80]
 for n,r in enumerate(tuple(rows)[:limit],1):
  x=interpret_trader_row(r);z += [f"#{n} {x.market_name}",f"   Oracle read: {x.takeaway}",f"   Direction: {x.direction} | Setup: {x.setup_quality}",f"   Historical knowledge: {x.historical_strength} | Live evidence: {x.live_evidence}",f"   Risk: {x.risk}",f"   Market ID: {x.market_id}",""]
 if not rows:z+=["No ranked markets in the current persisted snapshot."]
 return tuple(z+["No order placement. Q Series execution authority remains separate.","="*80])
