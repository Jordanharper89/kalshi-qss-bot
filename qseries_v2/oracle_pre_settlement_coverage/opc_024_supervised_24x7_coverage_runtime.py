from dataclasses import dataclass
from pathlib import Path
import time
from .opc_017_durable_coverage_runtime_state import load_coverage_runtime_state,save_coverage_runtime_state,advance_coverage_runtime_state
from .opc_019_coverage_recovery_health_supervision import is_transient_coverage_exception,evaluate_coverage_health
from .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget
from .opc_023_rotating_full_universe_coverage_cycle import run_rotating_full_universe_coverage_cycle
try:
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import PostgreSQLPersistenceRoutingFailure
except Exception:
    PostgreSQLPersistenceRoutingFailure=()

@dataclass(frozen=True)
class CoverageRuntimeCheck:
    ready:bool
    health:str
    terminal_dependency:bool=False
    execution_authority:bool=False

@dataclass(frozen=True)
class CoverageCycleSupervisionResult:
    status:str
    planned:int
    persisted:int
    retry_count:int
    transient_failure:bool
    exhausted:bool
    error_type:str=""
    execution_authority:bool=False

def _retryable(exc):
    if is_transient_coverage_exception(exc):
        return True
    try:
        if PostgreSQLPersistenceRoutingFailure and isinstance(exc,PostgreSQLPersistenceRoutingFailure):
            return True
    except TypeError:
        pass
    return type(exc).__name__=="PostgreSQLPersistenceRoutingFailure"

def _delay(attempt,base=.25,maximum=4.0):
    return min(float(maximum),float(base)*(2**max(0,int(attempt)-1)))

def run_one_supervised_coverage_cycle(root=None,budget=None,progress=None,cycle_fn=None,sleep_fn=time.sleep,max_retries=5):
    root=Path(root or Path.cwd()).resolve()
    budget=budget or CoverageLoadBudget()
    cycle_fn=cycle_fn or run_rotating_full_universe_coverage_cycle
    retries=0
    while True:
        try:
            r=cycle_fn(root,budget=budget,progress=progress)
            status="SUCCESS" if r.snapshots_planned==r.snapshots_persisted else "PARTIAL"
            return CoverageCycleSupervisionResult(status,r.snapshots_planned,r.snapshots_persisted,retries,False,False,"",False)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if not _retryable(exc):
                raise
            if retries>=int(max_retries):
                if progress:
                    progress(f"[COVERAGE RETRY] exhausted={max_retries} type={type(exc).__name__} action=record_failure_and_continue")
                return CoverageCycleSupervisionResult("TRANSIENT_FAILURE",0,0,retries,True,True,type(exc).__name__,False)
            retries+=1
            d=_delay(retries)
            if progress:
                progress(f"[COVERAGE RETRY] attempt={retries}/{max_retries} type={type(exc).__name__} delay={d:.2f}s")
            if d>0:
                sleep_fn(d)

def run_supervised_coverage_forever(root=None,budget=None,progress=None,sleep_fn=time.sleep):
    root=Path(root or Path.cwd()).resolve()
    budget=budget or CoverageLoadBudget()
    state=load_coverage_runtime_state(root)
    while True:
        try:
            r=run_one_supervised_coverage_cycle(root,budget,progress,sleep_fn=sleep_fn,max_retries=5)
            state=advance_coverage_runtime_state(state,planned=r.planned,persisted=r.persisted,status=r.status,transient_failure=r.transient_failure)
            state=save_coverage_runtime_state(state,root)
            health=evaluate_coverage_health(state)
            if progress:
                progress(f"[COVERAGE SUPERVISOR] status={r.status} planned={r.planned} persisted={r.persisted} retries={r.retry_count} health={health.health} consecutive_failures={state.consecutive_failures}")
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            state=advance_coverage_runtime_state(state,planned=0,persisted=0,status="FAILED",transient_failure=False)
            save_coverage_runtime_state(state,root)
            if progress:
                progress(f"[COVERAGE] fatal_failure type={type(exc).__name__} message={exc}")
            raise
        sleep_fn(float(budget.cycle_sleep_seconds))

def coverage_runtime_check(root=None):
    h=evaluate_coverage_health(load_coverage_runtime_state(root))
    return CoverageRuntimeCheck(h.health!="DEGRADED",h.health,False,False)

def verify_opc_024_supervised_24x7_coverage_runtime():
    calls={"n":0}
    class Result:
        snapshots_planned=100
        snapshots_persisted=100
    def flaky(root,budget=None,progress=None):
        calls["n"]+=1
        if calls["n"]<3:
            class PostgreSQLPersistenceRoutingFailure(Exception):
                pass
            raise PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")
        return Result()
    sleeps=[]
    r=run_one_supervised_coverage_cycle(".",CoverageLoadBudget(),cycle_fn=flaky,sleep_fn=lambda s:sleeps.append(s),max_retries=5)
    return r.status=="SUCCESS" and r.retry_count==2 and r.persisted==100 and len(sleeps)==2 and not r.execution_authority
