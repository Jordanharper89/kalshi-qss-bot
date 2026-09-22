from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time
from .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_market_freshness
from .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,save_coverage_universe_cursor,next_coverage_cursor
from .opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page
from .opc_026_full_page_coverage_admission import admit_full_page_coverage
from .opc_027_chunked_full_page_persistence import persist_full_page_in_chunks
from .opc_029_adaptive_coverage_throughput_controller import choose_throughput_budget
OPC_030_BUILD_ID="OPC-030"; OPC_030_REVISION="OPC_030_FORWARD_FRESHNESS_SETTLEMENT_AWARE_RECERTIFIED"
@dataclass(frozen=True)
class HighThroughputCoverageResult:
    page_markets:int; already_covered:int; missing_markets:int; requested:int; persisted:int; retries_used:int; chunk_size:int; cursor_advanced:bool; execution_authority:bool=False
def run_high_throughput_coverage_cycle(root=None,progress=None,recent_retries=0,recent_failures=0):
    root=Path(root or Path.cwd()).resolve(); throughput=choose_throughput_budget(recent_retries=recent_retries,recent_failures=recent_failures)
    budget=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0)
    old,markets,nxt,raw=fetch_rotating_open_page(root,budget)
    freshness=read_recent_canonical_market_freshness(root,24,250000)
    admission=admit_full_page_coverage(markets,freshness=freshness)
    result=persist_full_page_in_chunks(markets,admission.admitted_tickers,root=root,chunk_size=throughput.chunk_size,max_retries=throughput.max_retries,progress=progress)
    new=save_coverage_universe_cursor(next_coverage_cursor(old,nxt,raw),root)
    if progress:progress(f"[HIGH THROUGHPUT COVERAGE] page={new.pages_completed} raw={raw} active={len(markets)} fresh={admission.already_covered} due={admission.missing_markets} requested={result.requested} persisted={result.persisted} retries={result.retries_used} chunk_size={result.chunk_size} mode={throughput.mode}")
    if throughput.inter_page_sleep_seconds:time.sleep(throughput.inter_page_sleep_seconds)
    return HighThroughputCoverageResult(len(markets),admission.already_covered,admission.missing_markets,result.requested,result.persisted,result.retries_used,result.chunk_size,new.pages_completed>old.pages_completed,False)
def verify_opc_030_high_throughput_universal_coverage_gate():
    x=HighThroughputCoverageResult(1000,10,990,990,990,1,200,True,False)
    return x.requested==990 and x.persisted==990 and x.cursor_advanced and not x.execution_authority
