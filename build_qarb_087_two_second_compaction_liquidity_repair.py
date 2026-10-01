from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q86=S/"qarb_086_two_second_dynamic_execution_binding_cutover.py"
Q59=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py"
CORE=R/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"

M=S/"qarb_087_two_second_compaction_liquidity_repair.py"
T=R/"test_qarb_087_two_second_compaction_liquidity_repair.py"
U=R/"run_qarb_087_two_second_compaction_liquidity_repair.py"

for p in (Q86,Q59,CORE):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

s86=Q86.read_text(encoding="utf-8")
s59=Q59.read_text(encoding="utf-8")
score=CORE.read_text(encoding="utf-8")

guards=[
    ("086 memory candidates","def memory_candidates(" in s86),
    ("086 hydration","def hydrate(" in s86),
    ("q59 pump route","def api_pump_route(" in s59),
    ("q59 meteora ix","def dlmm_reverse_ix(" in s59),
    ("q59 candidates","def candidate_instruction_sets(" in s59),
    ("q59 mriya alts","def recent_mriya_alt_keys(" in s59),
    ("core compile","def compile_v0(" in score),
    ("core simulate","def simulate(" in score),
    ("core dlmm quote","def dlmm_quote(" in score),
]

bad=[name for name,ok in guards if not ok]
if bad:
    raise SystemExit(
        "[FAIL] current execution contract changed: "+repr(bad)
    )

module=r'''from __future__ import annotations

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
# buy / buyExactQuoteIn each have 23 fixed accounts.
PUMP_FIXED_ACCOUNTS=23

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
    if not recognized_pump_buy(ix):
        return None,0

    accounts=list(
        ix.get("accounts") or []
    )

    if len(accounts)<=PUMP_FIXED_ACCOUNTS:
        return None,0

    out=dict(ix)

    out["accounts"]=[
        dict(x)
        for x in accounts[
            :PUMP_FIXED_ACCOUNTS
        ]
    ]

    return (
        out,
        len(accounts)-PUMP_FIXED_ACCOUNTS
    )


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
'''

tests=r'''import base64
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q


class T(unittest.TestCase):

    def pump_ix(self,n=24,disc=None):
        disc=disc or q.BUY_EXACT_QUOTE_IN_DISC

        return {
            "programId":q.c.PUMP,
            "accounts":[
                {
                    "pubkey":"A%d"%i,
                    "isSigner":False,
                    "isWritable":False,
                }
                for i in range(n)
            ],
            "data":base64.b64encode(
                disc+b"\0"*24
            ).decode(),
        }


    def test_exact_pump_fixed_count(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            23
        )


    def test_buy_recognized(self):
        self.assertTrue(
            q.recognized_pump_buy(
                self.pump_ix(
                    23,
                    q.BUY_DISC
                )
            )
        )


    def test_buy_exact_quote_recognized(self):
        self.assertTrue(
            q.recognized_pump_buy(
                self.pump_ix(
                    23,
                    q.BUY_EXACT_QUOTE_IN_DISC
                )
            )
        )


    def test_only_trailing_optional_removed(self):
        ix=self.pump_ix(25)

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertEqual(n,2)

        self.assertEqual(
            len(z["accounts"]),
            23
        )


    def test_fixed_accounts_never_removed(self):
        ix=self.pump_ix(23)

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(z)

        self.assertEqual(n,0)


    def test_unknown_pump_instruction_not_trimmed(self):
        ix=self.pump_ix(
            30,
            b"\1\2\3\4\5\6\7\8"
        )

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(z)

        self.assertEqual(n,0)


    def test_alt_retry_not_duplicated(self):
        self.assertEqual(
            q.alt_sets([],[]),
            [[]]
        )


    def test_alt_retry_only_when_changed(self):
        self.assertEqual(
            q.alt_sets([],["X"]),
            [[],["X"]]
        )


    def test_size_ladder_descends(self):
        x=q.size_ladder(0.28)

        self.assertEqual(x[0],0.28)

        self.assertEqual(
            x,
            sorted(
                x,
                reverse=True
            )
        )


    def test_exact_086_boundary(self):
        self.assertTrue(
            callable(
                q.q86.memory_candidates
            )
        )

        self.assertTrue(
            callable(
                q.q86.hydrate
            )
        )


    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_087_two_second_compaction_liquidity_repair import main

if __name__=="__main__":
    raise SystemExit(main())
'''

M.write_text(
    module,
    encoding="utf-8"
)

T.write_text(
    tests,
    encoding="utf-8"
)

U.write_text(
    launcher,
    encoding="utf-8"
)

for p in (M,T,U):
    py_compile.compile(
        str(p),
        doraise=True
    )

print(
    "[PASS] QARB-087 in-place exact account-footprint repair installed"
)
print(
    "[PUMP] fixed 23-account contract preserved"
)
print(
    "[PUMP] only recognized trailing optional remaining accounts may be removed"
)
print(
    "[METEORA] exact published legacy swap account contract unchanged"
)
print(
    "[ALT] no duplicate retry when no real lookup table exists"
)
print(
    "[LOOP] repeated unchanged transaction-size fallback terminated"
)
print(
    "[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE"
)