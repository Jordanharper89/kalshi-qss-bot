from __future__ import annotations
import threading,time
from qseries_v2.oracle_execution import oracle_033_simulation_interface_compatibility_cutover as q33
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

LOCK=threading.Lock()
ATTACK_ROWS=[]
_ORIG_COMPOSE=None
_ORIG_ATTEMPT=None
_INSTALLED=False
_COMPOSE_MS={}

def _key(route):
    return (str(route.get("token") or ""),int(route.get("start_lamports") or 0))

def timed_compose(user,token,pump_pool,meteora_pool,start_sol):
    t0=time.perf_counter_ns()
    route=_ORIG_COMPOSE(user,token,pump_pool,meteora_pool,start_sol)
    ms=(time.perf_counter_ns()-t0)/1e6
    route=dict(route)
    route["token"]=token
    route["oracle034_compose_ms"]=ms
    with LOCK:
        _COMPOSE_MS[_key(route)]=ms
    return route

def positive_only_attempt(user,kp,route,blockhash):
    start_ns=time.perf_counter_ns()
    pre_net=int(route.get("pre_sim_net_lamports") or 0)
    pre_bps=float(route.get("pre_sim_bps") or 0.0)
    token=str(route.get("token") or "")
    size=float(route.get("start_lamports") or 0)/1e9

    if pre_net<=0 or pre_bps<=0:
        row={
            "token":token,"size_sol":size,"pre_sim_net_lamports":pre_net,
            "pre_sim_bps":pre_bps,"status":"NONPOSITIVE_NOT_ATTACKED",
            "execution_authority":False,
        }
        with LOCK: ATTACK_ROWS.append(row)
        print("[ORACLE034_SKIP_NONPOSITIVE] token=%s size=%.3f bps=%+.2f"%(
            token[:10],size,pre_bps
        ),flush=True)
        return None,[row]

    t1=time.perf_counter_ns()
    winner,rows=_ORIG_ATTEMPT(user,kp,route,blockhash)
    finished=time.perf_counter_ns()
    with LOCK:
        compose_ms=float(route.get("oracle034_compose_ms") or _COMPOSE_MS.get(_key(route),0.0))
    sim_ms=(finished-t1)/1e6
    total_ms=compose_ms+sim_ms
    rec={
        "token":token,
        "size_sol":size,
        "pre_sim_net_lamports":pre_net,
        "pre_sim_bps":pre_bps,
        "compose_ms":compose_ms,
        "simulation_lane_ms":sim_ms,
        "attack_total_ms":total_ms,
        "winner":winner,
        "attempt_count":len(rows),
        "profitable":bool(winner and winner.get("profitable")),
        "execution_authority":False,
    }
    with LOCK: ATTACK_ROWS.append(rec)
    print(
        "[ORACLE034_ATTACK] token=%s size=%.3f pre_bps=%+.2f "
        "compose_ms=%.3f sim_lane_ms=%.3f total_ms=%.3f profitable=%s"
        %(token[:10],size,pre_bps,compose_ms,sim_ms,total_ms,rec["profitable"]),
        flush=True,
    )
    return winner,rows

def install():
    global _ORIG_COMPOSE,_ORIG_ATTEMPT,_INSTALLED
    if _INSTALLED:return True
    q33.install()
    _ORIG_COMPOSE=q59.compose_reverse_candidates
    _ORIG_ATTEMPT=q59.attempt_candidate_simulations
    q59.compose_reverse_candidates=timed_compose
    q59.attempt_candidate_simulations=positive_only_attempt
    _INSTALLED=True
    return True

def run(seconds=300.0):
    install()
    from qseries_v2.oracle_execution import oracle_029_full_exact_pair_coverage_cutover as q29
    print("[ORACLE-034] POSITIVE-ONLY PAPER ATTACK LANE",flush=True)
    print("[ADMISSION] nonpositive composed routes cannot enter wealth simulation",flush=True)
    print("[TIMING] compose + simulation lane measured",flush=True)
    print("[BROADCAST] disabled",flush=True)
    return q29.run(seconds=seconds)
