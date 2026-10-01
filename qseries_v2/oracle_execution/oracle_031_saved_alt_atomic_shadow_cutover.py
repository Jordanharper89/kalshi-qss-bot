from __future__ import annotations
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.solana_live_execution import qarb_097_official_meteora_sdk_executor as q97

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232

_ORIG_COMPOSE=q59.compose_reverse_candidates
_ORIG_ATTEMPT=q59.attempt_candidate_simulations

def compose_with_token(user,token,pump_pool,meteora_pool,start_sol):
    route=_ORIG_COMPOSE(user,token,pump_pool,meteora_pool,start_sol)
    route=dict(route)
    route["token"]=token
    return route

def execution_route(route):
    return {
        "token":route.get("token"),
        "start_lamports":int(route["start_lamports"]),
        "pre_sim_net_lamports":int(route.get("pre_sim_net_lamports",0)),
        "pre_sim_bps":float(route.get("pre_sim_bps",0.0)),
        "base_alts":list(route.get("alts") or route.get("base_alts") or []),
        "original_candidates":list(route.get("candidates") or route.get("original_candidates") or []),
    }

def apply_saved_alt(root,route):
    before=list(route["base_alts"])
    result=q97._apply_saved_alt(Path(root),route)
    if isinstance(result,dict):
        route=result
    after=list(route.get("base_alts") or [])
    return route,before,after

def saved_alt_attempt_candidate_simulations(user,kp,route,blockhash):
    x=execution_route(route)
    token=x.get("token")
    x,before,after=apply_saved_alt(Path.cwd(),x)

    print("[ORACLE031_ALT] token=%s base_alts=%d saved_alts=%d"%(
        str(token)[:12],len(before),len(after)
    ),flush=True)

    candidates=list(q87.repaired_candidates(x))
    rows=[]

    for candidate in candidates:
        name=str(candidate.get("name",""))

        # Preserve QARB-097 live safety rule: helper-stripped shell is not executable authority.
        if "PUMP_METEORA_ONLY" in name:
            row={
                "name":name,
                "compiled":False,
                "bytes":None,
                "error":"LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
                "profitable":False,
            }
            rows.append(row)
            print("[ORACLE031_CANDIDATE] %s REJECT=%s"%(
                name,row["error"]
            ),flush=True)
            continue

        row=q87.simulate_candidate(
            user,
            kp,
            x,
            candidate,
            [list(x.get("base_alts") or [])],
            blockhash,
        )
        rows.append(row)

        print("[ORACLE031_CANDIDATE] %s compiled=%s bytes=%s alts=%s sim_err=%s pnl=%s bps=%s profitable=%s"%(
            name,
            row.get("compiled"),
            row.get("bytes"),
            row.get("alt_count"),
            row.get("sim_err"),
            row.get("sim_pnl_lamports"),
            row.get("sim_bps"),
            row.get("profitable"),
        ),flush=True)

        if (
            row.get("compiled")
            and int(row.get("bytes",MAX_TX_BYTES+1))<=MAX_TX_BYTES
            and row.get("sim_err") is None
            and row.get("profitable")
        ):
            return row,rows

    return None,rows

def install():
    q59.compose_reverse_candidates=compose_with_token
    q59.attempt_candidate_simulations=saved_alt_attempt_candidate_simulations
    return True

def run(seconds=300.0):
    install()
    from qseries_v2.oracle_execution import oracle_029_full_exact_pair_coverage_cutover as q29
    print("[ORACLE-031] SAVED-ALT ATOMIC SHADOW CUTOVER",flush=True)
    print("[ALT] QARB-097 saved ALT only; no Mriya lookup in hot path",flush=True)
    print("[CANDIDATES] QARB-087 repaired ladder",flush=True)
    print("[INPUT] ORACLE-028 exact-current positive handoff",flush=True)
    print("[MAX_TX_BYTES] 1232",flush=True)
    print("[BROADCAST] disabled",flush=True)
    return q29.run(seconds=seconds)

if __name__=="__main__":
    raise SystemExit(run())
