from pathlib import Path
from datetime import datetime,timezone
from qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page
from qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget
from qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import read_recent_canonical_market_freshness
from qseries_v2.oracle_pre_settlement_coverage.opc_028_activity_tier_refresh_policy import classify_market_refresh_tier
OPC_043_BUILD_ID="OPC-043"
def physical_probe(root=None):
 root=Path(root or Path.cwd()).resolve();now=datetime.now(timezone.utc);b=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0)
 _,markets,_,raw=fetch_rotating_open_page(root,b);fresh=read_recent_canonical_market_freshness(root,24,250000);rows=[];due=current=0
 for market in markets:
  t=str(market.get("ticker") or "");last=fresh.get(t);tier=classify_market_refresh_tier(market,now);age=None if last is None else max(0.0,(now-last).total_seconds());d=age is None or age>=tier.refresh_seconds;due+=int(d);current+=int(not d);rows.append((t,tier.tier,tier.refresh_seconds,None if age is None else round(age,1),d))
 return {"raw_page_markets":raw,"active_markets":len(markets),"with_recent_snapshot":sum(r[3] is not None for r in rows),"fresh_for_required_interval":current,"due_for_refresh":due,"sample":rows[:20],"read_only":True,"execution_authority":False}
def verify_opc_043():return OPC_043_BUILD_ID=="OPC-043"
