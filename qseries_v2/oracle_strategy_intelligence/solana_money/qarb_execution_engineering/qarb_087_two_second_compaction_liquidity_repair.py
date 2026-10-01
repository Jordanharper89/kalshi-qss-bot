from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_086_two_second_dynamic_execution_binding_cutover as q86


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_087_two_second_compaction_liquidity_repair.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

BUY_DISC=bytes([
    102,6,61,18,1,218,235,234
])

BUY_EXACT_QUOTE_IN_DISC=bytes([
    198,46,21,82,180,217,232,112
])

# PumpSwap published IDL:
# Current physical PumpSwap contract requires 24 accounts; account 24 preserves pool_v2.
PUMP_FIXED_ACCOUNTS=26

SIZE_GRID=(
    1.4,1.1,0.9,0.5,0.28,
    0.18,0.1,0.05,0.025,
    0.01,0.005
)


def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=path.with_suffix(
        path.suffix+".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    tmp.replace(path)


def discriminator(ix):
    try:
        return base64.b64decode(
            ix.get("data") or ""
        )[:8]
    except Exception:
        return b""


def recognized_pump_buy(ix):
    if ix.get("programId")!=c.PUMP:
        return False

    return discriminator(ix) in (
        BUY_DISC,
        BUY_EXACT_QUOTE_IN_DISC
    )


def trim_optional_pump_accounts(ix):
    """
    SAE-011:
    PumpSwap remaining accounts are dynamic protocol accounts.

    The installed PumpSwap SDK appends required accounts including
    pool_v2, buyback fee recipient, buyback recipient ATA, and
    potentially other feature-gated remaining accounts.

    Therefore account-count slicing is not a safe compaction method.
    Preserve the instruction exactly.
    """
    if not recognized_pump_buy(ix):
        return None,0

    return None,0



def size_ladder(preferred):
    preferred=float(preferred)

    out=[preferred]

    for x in SIZE_GRID:
        if x < preferred-1e-12:
            out.append(float(x))

    clean=[]
    seen=set()

    for x in out:
        k=round(x,9)

        if k in seen:
            continue

        seen.add(k)
        clean.append(k)

    return clean


def bound_meta(pair):
    return {
        "address":pair.meteora_pool,
        "token_x":pair.token_x,
        "token_y":pair.token_y,
        "decimals_x":pair.decimals_x,
        "decimals_y":pair.decimals_y,
    }


def exact_quote(pair,amount_in):
    try:
        q=las._live_dlmm_quote(
            pair,
            amount_in,
            pair.token
        )

        q["source"]="HYDRATED"

        return q

    except RuntimeError as exc:
        if str(exc)!="DLMM_PARTIAL":
            raise

    q=c.dlmm_quote(
        bound_meta(pair),
        amount_in,
        pair.token
    )

    q["source"]="FULL_BOUND_REFRESH"

    return q


def compose(user,pair,size_sol):
    start=int(
        round(float(size_sol)*1e9)
    )

    p_ixs,base_alts,pump_out=(
        las.q59.api_pump_route(
            user,
            pair.token,
            start
        )
    )

    pump_indexes=[
        i
        for i,x in enumerate(p_ixs)
        if x.get("programId")==c.PUMP
    ]

    if len(pump_indexes)!=1:
        raise RuntimeError(
            "PUMP_PROGRAM_IX_COUNT:"
            +str(len(pump_indexes))
        )

    pump_index=pump_indexes[0]
    pump_ix=p_ixs[pump_index]

    if not any(
        a.get("pubkey")==pair.pump_pool
        for a in pump_ix.get("accounts") or []
    ):
        raise RuntimeError(
            "PUMP_BINDING_DRIFT"
        )

    quote=exact_quote(
        pair,
        pump_out
    )

    meteora_ix=las.q59.dlmm_reverse_ix(
        user,
        bound_meta(pair),
        pump_out,
        quote
    )

    end=int(
        quote["raw_out"]
    )

    return {
        "start_lamports":start,
        "pre_sim_net_lamports":
            end-start,
        "pre_sim_bps":
            (end-start)/start*10000.0,
        "quote_source":
            quote.get("source"),
        "bins_crossed":
            int(
                quote.get(
                    "bins_crossed",
                    1
                )
            ),
        "pump_ixs":p_ixs,
        "pump_index":pump_index,
        "pump_ix":pump_ix,
        "meteora_ix":meteora_ix,
        "base_alts":list(base_alts),
        "original_candidates":
            las.q59.candidate_instruction_sets(
                p_ixs,
                meteora_ix
            ),
    }


def repaired_candidates(route):
    out=[]
    seen=set()

    def add(name,ixs,removed=0):
        key=tuple(
            (
                x.get("programId"),
                x.get("data"),
                tuple(
                    a.get("pubkey")
                    for a in
                    (x.get("accounts") or [])
                )
            )
            for x in ixs
        )

        if key in seen:
            return

        seen.add(key)

        for _ix in ixs:
            if _ix.get("programId")!=c.PUMP:
                continue
            _aa=list(_ix.get("accounts") or [])
            print(
                "[SAE008B_CANDIDATE] name=%s total=%d removed=%d"%(
                    name,len(_aa),int(removed)
                ),
                flush=True
            )
            for _i in range(max(0,len(_aa)-3),len(_aa)):
                _a=_aa[_i]
                print(
                    "[SAE008B_ACCOUNT] name=%s number=%d pubkey=%s writable=%s"%(
                        name,
                        _i+1,
                        _a.get("pubkey"),
                        _a.get("isWritable"),
                    ),
                    flush=True
                )

        out.append({
            "name":name,
            "instructions":ixs,
            "pump_optional_removed":
                int(removed),
        })

    # Preserve all existing exact candidates.
    for name,ixs in route[
        "original_candidates"
    ]:
        add(
            name,
            list(ixs),
            0
        )

        pump_pos=[
            i
            for i,x in enumerate(ixs)
            if x.get("programId")==c.PUMP
        ]

        if len(pump_pos)!=1:
            continue

        pi=pump_pos[0]

        trimmed,removed=(
            trim_optional_pump_accounts(
                ixs[pi]
            )
        )

        if trimmed is None:
            continue

        z=list(ixs)
        z[pi]=trimmed

        add(
            "PUMP_OPTIONAL_TRIM_"+name,
            z,
            removed
        )

    return out


def alt_sets(base_alts,extra_alts):
    first=list(
        dict.fromkeys(
            base_alts
        )
    )

    second=list(
        dict.fromkeys(
            first+extra_alts
        )
    )

    out=[first]

    # Never rerun identical empty/no-op ALT set.
    if second!=first:
        out.append(second)

    return out


def compile_candidate(
    user,
    ixs,
    alt_options,
    blockhash
):
    attempts=[]

    for alts in alt_options:
        try:
            msg,unsigned=c.compile_v0(
                user,
                ixs,
                alts,
                blockhash
            )

            return {
                "ok":True,
                "msg":msg,
                "unsigned":unsigned,
                "bytes":len(unsigned),
                "alts":alts,
                "attempts":attempts,
            }

        except RuntimeError as exc:
            txt=str(exc)

            attempts.append({
                "alts":len(alts),
                "error":txt,
            })

            if not txt.startswith(
                "ATOMIC_TX_TOO_LARGE:"
            ):
                return {
                    "ok":False,
                    "error":txt,
                    "attempts":attempts,
                }

    return {
        "ok":False,
        "error":(
            attempts[-1]["error"]
            if attempts
            else "NO_COMPILE_ATTEMPT"
        ),
        "attempts":attempts,
    }


def simulate_candidate(
    user,
    kp,
    route,
    candidate,
    alt_options,
    blockhash
):
    comp=compile_candidate(
        user,
        candidate["instructions"],
        alt_options,
        blockhash
    )

    row={
        "name":candidate["name"],
        "pump_optional_removed":
            candidate[
                "pump_optional_removed"
            ],
        "compiled":
            bool(comp.get("ok")),
        "compile_attempts":
            comp.get("attempts",[]),
    }

    if not comp.get("ok"):
        row["error"]=comp.get("error")
        return row

    raw=(
        c.signed_tx(
            comp["msg"],
            kp
        )
        if kp is not None
        else comp["unsigned"]
    )

    row["bytes"]=len(raw)
    row["alt_count"]=len(
        comp["alts"]
    )

    sim=c.simulate(
        raw,
        user,
        sigverify=(
            kp is not None
        )
    )

    pnl=sim.get("pnl")

    bps=(
        pnl
        /route["start_lamports"]
        *10000.0
        if pnl is not None
        else None
    )

    row.update({
        "sim_err":sim.get("err"),
        "sim_units":sim.get("units"),
        "sim_pnl_lamports":pnl,
        "sim_bps":bps,
        "profitable":bool(
            sim.get("err") is None
            and pnl is not None
            and pnl>0
            and bps>=las.q59.MIN_NET_BPS
        )
    })

    return row


def diagnostic(row):
    if row.get("profitable"):
        return "PROFITABLE_SIMULATION"

    if not row.get("compiled"):
        return (
            "COMPILE_FAIL:"
            +str(row.get("error"))
        )

    if row.get("sim_err") is not None:
        return (
            "SIM_ERROR:"
            +str(row.get("sim_err"))
        )

    if row.get(
        "sim_pnl_lamports"
    ) is None:
        return "SIM_PNL_UNAVAILABLE"

    if row[
        "sim_pnl_lamports"
    ]<=0:
        return "SIM_PNL_NONPOSITIVE"

    if row.get("sim_bps") is None:
        return "SIM_BPS_UNAVAILABLE"

    if row[
        "sim_bps"
    ]<las.q59.MIN_NET_BPS:
        return "SIM_BPS_BELOW_GATE"

    return "UNCLASSIFIED_REJECT"


def run(root=None):
    root=Path(root or Path.cwd())

    bindings,audit=q86.memory_candidates(
        root
    )

    print(
        "[QARB-087] IN-PLACE 2S "
        "ATOMIC SIZE REPAIR",
        flush=True
    )

    print(
        "[PUMP] only published optional "
        "trailing remaining accounts may be trimmed",
        flush=True
    )

    print(
        "[METEORA] published legacy swap "
        "account contract preserved",
        flush=True
    )

    if not bindings:
        print(
            "[QARB-087 HOLD] "
            "no qualified 2s bindings",
            flush=True
        )
        return 2

    pairs,_=q86.hydrate(
        root,
        bindings
    )

    pair_map={
        p.token:p
        for p in pairs
    }

    kp,user=c.sim_identity()

    # Discover possible real chain ALTs ONCE.
    # If none exist, there is no pointless retry.
    try:
        extra_alts=(
            las.q59.recent_mriya_alt_keys()
        )
    except Exception:
        extra_alts=[]

    print(
        "[ALT_DISCOVERY] found=%d"%(
            len(extra_alts)
        ),
        flush=True
    )

    results={}

    compiled_tokens=0
    simulated_tokens=0
    profitable_tokens=0

    for binding in bindings:
        token=binding["token"]
        pair=pair_map.get(token)

        r={
            "token":token,
            "preferred_size_sol":
                binding["size_sol"],
            "sizes":[],
        }

        results[token]=r

        if pair is None:
            r["status"]="PAIR_MISSING"
            continue

        compiled=False
        simulated=False
        winner=None

        previous_min_bytes=None
        unchanged_oversize=0

        for size in size_ladder(
            binding["size_sol"]
        ):
            sr={
                "size_sol":size
            }

            r["sizes"].append(sr)

            try:
                route=compose(
                    user,
                    pair,
                    size
                )

            except RuntimeError as exc:
                sr["compose_error"]=str(exc)

                if str(exc)=="DLMM_PARTIAL":
                    sr["diagnostic"]="DLMM_PARTIAL"
                    continue

                sr["diagnostic"]="COMPOSE_ERROR"
                break

            sr[
                "pre_sim_net_sol"
            ]=(
                route[
                    "pre_sim_net_lamports"
                ]/1e9
            )

            sr[
                "pre_sim_bps"
            ]=route[
                "pre_sim_bps"
            ]

            sr[
                "bins_crossed"
            ]=route[
                "bins_crossed"
            ]

            sr[
                "pump_accounts"
            ]=len(
                route[
                    "pump_ix"
                ].get(
                    "accounts"
                ) or []
            )

            if route[
                "pre_sim_net_lamports"
            ]<=0:
                sr[
                    "diagnostic"
                ]="PRE_SIM_NONPOSITIVE"
                continue

            bh=c.rpc(
                "getLatestBlockhash",
                [{
                    "commitment":
                        "processed"
                }]
            )["value"]["blockhash"]

            options=alt_sets(
                route["base_alts"],
                extra_alts
            )

            attempts=[]

            for candidate in repaired_candidates(
                route
            ):
                row=simulate_candidate(
                    user,
                    kp,
                    route,
                    candidate,
                    options,
                    bh
                )

                row[
                    "diagnostic"
                ]=diagnostic(
                    row
                )

                attempts.append(
                    row
                )

                if row.get("compiled"):
                    compiled=True

                if (
                    row.get("compiled")
                    and "sim_err" in row
                ):
                    simulated=True

                if row.get("profitable"):
                    winner={
                        "size_sol":size,
                        **row,
                    }
                    break

            sr["attempts"]=attempts

            legal=[
                x
                for x in attempts
                if x.get("compiled")
            ]

            if winner:
                break

            if legal:
                # We crossed the size wall.
                # No need to search smaller just for bytes.
                break

            sizes=[]

            for x in attempts:
                for ca in x.get(
                    "compile_attempts",
                    []
                ):
                    txt=ca.get("error","")

                    if txt.startswith(
                        "ATOMIC_TX_TOO_LARGE:"
                    ):
                        try:
                            sizes.append(
                                int(
                                    txt.rsplit(
                                        ":",
                                        1
                                    )[1]
                                )
                            )
                        except Exception:
                            pass

            current_min=(
                min(sizes)
                if sizes
                else None
            )

            if (
                current_min is not None
                and current_min
                    ==previous_min_bytes
            ):
                unchanged_oversize+=1
            else:
                unchanged_oversize=0

            previous_min_bytes=(
                current_min
            )

            # Two consecutive smaller sizes with
            # identical minimum bytes proves size
            # reduction is not changing account footprint.
            if unchanged_oversize>=2:
                sr[
                    "diagnostic"
                ]="SIZE_FOOTPRINT_UNCHANGED_STOP"
                break

        if compiled:
            compiled_tokens+=1

        if simulated:
            simulated_tokens+=1

        if winner:
            profitable_tokens+=1
            r["winner"]=winner
            r[
                "status"
            ]="EXECUTABLE_2S_SIM_PASS"

        elif simulated:
            r[
                "status"
            ]="SIMULATED_NO_PROFIT"

        elif compiled:
            r[
                "status"
            ]="COMPILED_NO_VALID_SIM"

        else:
            r[
                "status"
            ]="NO_LEGAL_COMPILED_CANDIDATE"

    status=(
        "PASS"
        if simulated_tokens>0
        else "HOLD"
    )

    out={
        "revision":"QARB_087_REPAIR",
        "status":status,
        "qualified_tokens":
            len(bindings),
        "hydrated_tokens":
            len(pairs),
        "alt_discovery_count":
            len(extra_alts),
        "compiled_tokens":
            compiled_tokens,
        "simulated_tokens":
            simulated_tokens,
        "profitable_tokens":
            profitable_tokens,
        "results":results,
        "binding_audit":audit,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "created_unix":time.time(),
    }

    _save(
        root/STATE,
        out
    )

    for token,r in results.items():
        print(
            "[2S_EXEC] token=%s preferred=%.6f status=%s"%(
                token[:10],
                r["preferred_size_sol"],
                r["status"]
            ),
            flush=True
        )

        for sr in r["sizes"]:
            if sr.get("compose_error"):
                print(
                    "[2S_SIZE] token=%s size=%.6f %s"%(
                        token[:10],
                        sr["size_sol"],
                        sr["compose_error"]
                    ),
                    flush=True
                )
                continue

            attempts=sr.get(
                "attempts",
                []
            )

            if not attempts:
                continue

            best=min(
                (
                    x["bytes"]
                    for x in attempts
                    if x.get("compiled")
                ),
                default=None
            )

            overs=[]

            for x in attempts:
                for ca in x.get(
                    "compile_attempts",
                    []
                ):
                    e=ca.get("error","")

                    if e.startswith(
                        "ATOMIC_TX_TOO_LARGE:"
                    ):
                        try:
                            overs.append(
                                int(
                                    e.rsplit(
                                        ":",
                                        1
                                    )[1]
                                )
                            )
                        except Exception:
                            pass

            smallest=(
                min(overs)
                if overs
                else None
            )

            removed=max(
                (
                    x.get(
                        "pump_optional_removed",
                        0
                    )
                    for x in attempts
                ),
                default=0
            )

            print(
                "[2S_SIZE_RESULT] token=%s "
                "size=%.6f pump_accounts=%s "
                "optional_removed=%d "
                "legal_bytes=%s "
                "smallest_oversize=%s"%(
                    token[:10],
                    sr["size_sol"],
                    sr.get("pump_accounts"),
                    removed,
                    best,
                    smallest
                ),
                flush=True
            )

            for x in attempts:
                if (
                    x.get("compiled")
                    or x.get(
                        "pump_optional_removed",
                        0
                    )>0
                ):
                    print(
                        "[2S_ATOMIC] token=%s "
                        "candidate=%s "
                        "removed=%d bytes=%s "
                        "alts=%s sim_err=%s "
                        "pnl=%s bps=%s "
                        "diagnostic=%s"%(
                            token[:10],
                            x["name"],
                            x.get(
                                "pump_optional_removed",
                                0
                            ),
                            x.get("bytes"),
                            x.get("alt_count"),
                            x.get("sim_err"),
                            x.get(
                                "sim_pnl_lamports"
                            ),
                            x.get("sim_bps"),
                            x["diagnostic"]
                        ),
                        flush=True
                    )

        if r.get("winner"):
            w=r["winner"]

            print(
                "[2S_EXECUTABLE_PROFIT] "
                "token=%s size=%.6f "
                "candidate=%s bytes=%d "
                "sim=%+.9f_SOL bps=%+.2f"%(
                    token[:10],
                    w["size_sol"],
                    w["name"],
                    w["bytes"],
                    w[
                        "sim_pnl_lamports"
                    ]/1e9,
                    w["sim_bps"]
                ),
                flush=True
            )

    print(
        "[QARB-087] status=%s "
        "qualified=%d hydrated=%d "
        "compiled=%d simulated=%d "
        "profitable=%d"%(
            status,
            len(bindings),
            len(pairs),
            compiled_tokens,
            simulated_tokens,
            profitable_tokens
        ),
        flush=True
    )

    print(
        "[MODE] simulation_only "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return 0 if status=="PASS" else 2


def main():
    return run(Path.cwd())


if __name__=="__main__":
    raise SystemExit(main())
