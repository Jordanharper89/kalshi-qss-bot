from __future__ import annotations
from pathlib import Path

from qseries_v2.oracle_execution import oracle_031_saved_alt_atomic_shadow_cutover as q31
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_088_two_second_executable_profit_accounting as q88

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232

def keyless_measured_candidate(user, route, candidate, alt_options, blockhash, token):
    comp=q87.compile_candidate(
        user,
        candidate["instructions"],
        alt_options,
        blockhash,
    )

    row={
        "name":candidate["name"],
        "pump_optional_removed":candidate.get("pump_optional_removed",0),
        "compiled":bool(comp.get("ok")),
        "compile_attempts":comp.get("attempts",[]),
    }

    if not comp.get("ok"):
        row["error"]=comp.get("error")
        return row

    # KEYLESS PHYSICAL RULE:
    # compile_v0 already returns a transaction with a zeroed signature slot.
    # Use it directly with sigVerify=False. Never invoke signed_tx here.
    raw=comp["unsigned"]
    row["bytes"]=len(raw)
    row["alt_count"]=len(comp.get("alts") or [])

    if len(raw)>MAX_TX_BYTES:
        row["error"]="TX_TOO_LARGE_UNSIGNED"
        return row

    sim=q88.simulate_wealth(
        raw,
        comp["msg"],
        user,
        token,
        sigverify=False,
    )

    gross=sim["gross_wealth_delta_lamports"]
    net=sim["net_after_fee_lamports"]

    gross_bps=(
        gross/route["start_lamports"]*10000.0
        if gross is not None
        else None
    )
    net_bps=(
        net/route["start_lamports"]*10000.0
        if net is not None
        else None
    )

    profitable=bool(
        sim["err"] is None
        and net is not None
        and net>0
        and net_bps is not None
        and net_bps>=q59.MIN_NET_BPS
        and sim["residual_token_delta_raw"]==0
    )

    row.update({
        "sim_err":sim["err"],
        "sim_units":sim["units"],
        "gross_sim_pnl_lamports":gross,
        "gross_sim_bps":gross_bps,
        "estimated_fee_lamports":sim["estimated_fee_lamports"],
        "net_sim_pnl_lamports":net,
        "net_sim_bps":net_bps,
        "residual_token_delta_raw":sim["residual_token_delta_raw"],
        "pre_native_lamports":sim["pre_native_lamports"],
        "post_native_lamports":sim["post_native_lamports"],
        "pre_wsol_amount":sim.get("pre_wsol_amount"),
        "post_wsol_amount":sim.get("post_wsol_amount"),
        "profitable_after_fee":profitable,
        "profitable":profitable,
        "sim_pnl_lamports":net,
        "sim_bps":net_bps,
    })
    return row

def wealth_attempt_candidate_simulations(user,kp,route,blockhash):
    x=q31.execution_route(route)
    token=x.get("token")

    if not token:
        print("[ORACLE032_SKIP] reason=NO_EXACT_TOKEN_CONTEXT",flush=True)
        return None,[{
            "name":"LEGACY_NO_TOKEN_CONTEXT",
            "compiled":False,
            "error":"NO_EXACT_TOKEN_CONTEXT",
            "profitable":False,
        }]

    # Enforce keyless boundary regardless of caller state.
    if kp is not None:
        print("[ORACLE032_KEYLESS_GUARD] caller_key_ignored=True",flush=True)

    x,before,after=q31.apply_saved_alt(Path.cwd(),x)

    print("[ORACLE032_ALT] token=%s base_alts=%d saved_alts=%d"%(
        str(token)[:12],len(before),len(after)
    ),flush=True)

    candidates=list(q87.repaired_candidates(x))
    rows=[]

    for candidate in candidates:
        name=str(candidate.get("name",""))

        if "PUMP_METEORA_ONLY" in name:
            row={
                "name":name,
                "compiled":False,
                "error":"LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
                "profitable":False,
            }
            rows.append(row)
            print("[ORACLE032_CANDIDATE] %s REJECT=%s"%(name,row["error"]),flush=True)
            continue

        row=keyless_measured_candidate(
            user,
            x,
            candidate,
            [list(x.get("base_alts") or [])],
            blockhash,
            token,
        )
        rows.append(row)

        print(
            "[ORACLE032_WEALTH_SIM] token=%s candidate=%s compiled=%s bytes=%s "
            "err=%s gross=%s fee=%s net=%s bps=%s residual_token=%s profitable=%s"
            % (
                str(token)[:10],
                name,
                row.get("compiled"),
                row.get("bytes"),
                row.get("sim_err"),
                row.get("gross_sim_pnl_lamports"),
                row.get("estimated_fee_lamports"),
                row.get("net_sim_pnl_lamports"),
                row.get("net_sim_bps"),
                row.get("residual_token_delta_raw"),
                row.get("profitable_after_fee"),
            ),
            flush=True,
        )

        if row.get("profitable_after_fee"):
            return row,rows

    return None,rows

def install():
    q31.install()
    q59.attempt_candidate_simulations=wealth_attempt_candidate_simulations
    return True

def run(seconds=300.0):
    install()
    from qseries_v2.oracle_execution import oracle_029_full_exact_pair_coverage_cutover as q29

    print("[ORACLE-032] FULL REPLACEMENT KEYLESS EXECUTABLE WEALTH ACCOUNTING",flush=True)
    print("[PACKET] ORACLE-031 compact <=1232-byte path preserved",flush=True)
    print("[SIGNER] prohibited; compiled unsigned transaction used directly",flush=True)
    print("[SIM] sigVerify=False",flush=True)
    print("[ACCOUNTING] QARB-088 corrected wealth simulator",flush=True)
    print("[FEE] getFeeForMessage measured separately",flush=True)
    print("[RESIDUAL] intermediate token delta must equal zero",flush=True)
    print("[BROADCAST] disabled",flush=True)

    return q29.run(seconds=seconds)

if __name__=="__main__":
    raise SystemExit(run())
