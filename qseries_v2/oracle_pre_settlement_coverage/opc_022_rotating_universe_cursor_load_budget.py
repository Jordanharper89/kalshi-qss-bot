from dataclasses import asdict,dataclass
from pathlib import Path
from hashlib import sha256
import json,os
@dataclass(frozen=True)
class CoverageLoadBudget:
    page_limit:int=1000
    max_snapshots_per_cycle:int=100
    cycle_sleep_seconds:float=30.0
    lookback_hours:float=24.0
    request_timeout_seconds:float=20.0
@dataclass(frozen=True)
class CoverageUniverseCursor:
    cursor:str=""
    pages_completed:int=0
    markets_seen:int=0
    cycles_completed:int=0
    last_page_markets:int=0
    terminal_wraps:int=0
    state_hash:str=""
def coverage_cursor_path(root=None): return Path(root or Path.cwd()).resolve()/"runtime_state"/"oracle_pre_settlement_coverage_universe_cursor.json"
def _hash(d):
    x=dict(d);x["state_hash"]=""
    return sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def load_coverage_universe_cursor(root=None):
    p=coverage_cursor_path(root)
    return CoverageUniverseCursor(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else CoverageUniverseCursor()
def save_coverage_universe_cursor(state,root=None):
    p=coverage_cursor_path(root);p.parent.mkdir(parents=True,exist_ok=True)
    d=asdict(state);d["state_hash"]=_hash(d)
    t=p.with_suffix(".json.tmp");t.write_text(json.dumps(d,sort_keys=True,indent=2),encoding="utf-8");os.replace(t,p)
    return CoverageUniverseCursor(**d)
def next_coverage_cursor(state,next_cursor,page_markets):
    return CoverageUniverseCursor(str(next_cursor or ""),state.pages_completed+1,state.markets_seen+int(page_markets),state.cycles_completed+1,int(page_markets),state.terminal_wraps+(0 if next_cursor else 1),"")
def verify_opc_022_rotating_universe_cursor_load_budget():
    b=CoverageLoadBudget();s=next_coverage_cursor(CoverageUniverseCursor(),"abc",1000);w=next_coverage_cursor(s,"",250)
    return b.page_limit==1000 and b.max_snapshots_per_cycle==100 and s.cursor=="abc" and w.terminal_wraps==1
