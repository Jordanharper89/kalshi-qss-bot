from __future__ import annotations
from pathlib import Path

from qseries_v2.oracle_execution import oracle_031_saved_alt_atomic_shadow_cutover as q31
from qseries_v2.oracle_execution import oracle_033_simulation_interface_compatibility_cutover as q33
from qseries_v2.oracle_execution import oracle_034_positive_only_paper_attack_lane as q34
from qseries_v2.oracle_execution import oracle_037_positive_paper_attack_certification as q37
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59

q87=q33.q32.q87
q88=q33.q32.q88

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232

def compile_isolated(user,candidate,alt_options,blockhash):
    name=str(candidate.get("name","UNKNOWN"))
    try:
        comp=q87.compile_candidate(
            user,
            candidate["instructions"],
            alt_options,
            blockhash,
        )
        if not isinstance(comp,dict):
            return {
                "ok":False,
                "error":"COMPILE_RETURN_NOT_MAPPING:%s"%type(comp).__name__,
                "attempts":[],
            }
        return comp
    except Exception as exc:
        primary="%s:%s"%(type(exc).__name__,str(exc))
        try:
            for alts in alt_options:
                try:
                    msg,unsigned=q87.c.compile_v0(
                        user,
                        candidate["instructions"],
                        alts,
                        blockhash,
                    )
                    return {
                        "ok":True,
                        "msg":msg,
                        "unsigned":unsigned,
                        "bytes":len(unsigned),
                        "alts":alts,
                        "attempts":[{"fallback_after":primary}],
                    }
                except Exception:
                    continue
        except Exception:
            pass
        return {
            "ok":False,
            "error":primary,
            "attempts":[],
        }

def measure(user,route,candidate,alt_options,blockhash,token):
    name=str(candidate.get("name","UNKNOWN"))
    comp=compile_isolated(user,candidate,alt_options,blockhash)

    row={
        "name":name,
        "compiled":bool(comp.get("ok")),
        "compile_attempts":comp.get("attempts",[]),
        "error":comp.get("error"),
        "profitable":False,
    }

    if not comp.get("ok"):
        return row

    raw=comp["unsigned"]
    row["bytes"]=len(raw)
    row["alt_count"]=len(comp.get("alts") or [])

    if len(raw)>MAX_TX_BYTES:
        row["compiled"]=False
        row["error"]="TX_TOO_LARGE:%d"%len(raw)
        return row

    try:
        sim=q88.simulate_wealth(
            raw,
            comp["msg"],
            user,
            token,
            False,
        )
    except Exception as exc:
        row["sim_err"]="WEALTH_SIM_EXCEPTION:%s:%s"%(
            type(exc).__name__,
            str(exc),
        )
        return row

    if not isinstance(sim,dict):
        row["sim_err"]="WEALTH_SIM_RETURN_NOT_MAPPING:%s"%type(sim).__name__
        return row

    gross=sim.get("gross_wealth_delta_lamports")
    net=sim.get("net_after_fee_lamports")
    residual=sim.get("residual_token_delta_raw")
    fee=sim.get("estimated_fee_lamports")
    err=sim.get("err")

    net_bps=(
        net/route["start_lamports"]*10000.0
        if net is not None
        else None
    )

    good=bool(
        err is None
        and net is not None
        and net>0
        and net_bps is not None
        and net_bps>=q59.MIN_NET_BPS
        and residual==0
    )

    row.update({
        "sim_err":err,
        "sim_units":sim.get("units"),
        "gross_sim_pnl_lamports":gross,
        "estimated_fee_lamports":fee,
        "net_sim_pnl_lamports":net,
        "net_sim_bps":net_bps,
        "residual_token_delta_raw":residual,
        "profitable_after_fee":good,
        "profitable":good,
        "sim_pnl_lamports":net,
        "sim_bps":net_bps,
    })
    return row

def isolated_attack(user,kp,route,blockhash):
    x=q31.execution_route(route)
    token=x.get("token")

    if not token:
        return None,[{
            "name":"NO_TOKEN_CONTEXT",
            "compiled":False,
            "error":"NO_EXACT_TOKEN_CONTEXT",
            "profitable":False,
        }]

    x,before,after=q31.apply_saved_alt(Path.cwd(),x)

    base=list(x.get("base_alts") or [])
    alt_options=[base]

    print(
        "[ORACLE038_ALT] token=%s base_alts=%d saved_alts=%d"
        %(str(token)[:12],len(before),len(after)),
        flush=True,
    )

    rows=[]
    candidates=list(q87.repaired_candidates(x))

    for index,candidate in enumerate(candidates,1):
        name=str(candidate.get("name","UNKNOWN"))

        if "PUMP_METEORA_ONLY" in name:
            row={
                "name":name,
                "compiled":False,
                "error":"LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
                "profitable":False,
            }
        else:
            row=measure(
                user,
                x,
                candidate,
                alt_options,
                blockhash,
                token,
            )

        rows.append(row)

        print(
            "[ORACLE038_CANDIDATE] n=%d token=%s name=%s "
            "compiled=%s bytes=%s error=%s sim_err=%s "
            "gross=%s fee=%s net=%s bps=%s residual=%s profitable=%s"
            %(
                index,
                str(token)[:10],
                name,
                row.get("compiled"),
                row.get("bytes"),
                row.get("error"),
                row.get("sim_err"),
                row.get("gross_sim_pnl_lamports"),
                row.get("estimated_fee_lamports"),
                row.get("net_sim_pnl_lamports"),
                row.get("net_sim_bps"),
                row.get("residual_token_delta_raw"),
                row.get("profitable"),
            ),
            flush=True,
        )

        if row.get("compiled") and row.get("net_sim_pnl_lamports") is not None:
            print(
                "[ORACLE038_EXECUTABLE_MEASUREMENT] token=%s candidate=%s "
                "bytes=%s net=%s bps=%s profitable=%s"
                %(
                    str(token)[:10],
                    name,
                    row.get("bytes"),
                    row.get("net_sim_pnl_lamports"),
                    row.get("net_sim_bps"),
                    row.get("profitable"),
                ),
                flush=True,
            )

        if row.get("profitable"):
            return row,rows

    return None,rows

def install():
    q33.attack=isolated_attack

    q34._INSTALLED=False
    q34._ORIG_COMPOSE=None
    q34._ORIG_ATTEMPT=None

    return True

def run(seconds=300.0):
    install()

    print(
        "[ORACLE-038] CANDIDATE COMPILE ISOLATION + COMPACT RECOVERY",
        flush=True,
    )
    print(
        "[TARGET] PUMP_OPTIONAL_TRIM_NO_COMPUTE_MEMO",
        flush=True,
    )
    print(
        "[RULE] one failed candidate cannot abort repaired candidate ladder",
        flush=True,
    )
    print(
        "[SIM] first <=1232-byte compiled candidate reaches wealth accounting",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)

    return q37.run(seconds=seconds)
