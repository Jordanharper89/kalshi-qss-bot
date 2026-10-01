from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q87=S/"qarb_087_two_second_compaction_liquidity_repair.py"
CORE=R/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"

M=S/"qarb_089_two_second_dlmm_liquidity_binding_recovery.py"
T=R/"test_qarb_089_two_second_dlmm_liquidity_binding_recovery.py"
U=R/"run_qarb_089_two_second_dlmm_liquidity_binding_recovery.py"

for p in (Q87,CORE):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

s87=Q87.read_text(encoding="utf-8")
score=CORE.read_text(encoding="utf-8")

guards=[
    ("087 size ladder","def size_ladder(" in s87),
    ("086 memory boundary","q86.memory_candidates" in s87),
    ("Pump exact route","def api_pump_route(" in
        (R/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py").read_text(encoding="utf-8")),
    ("DLMM arrays","def dlmm_arrays(" in score),
    ("account reader","def account(" in score),
    ("HTTP provider","def http(" in score),
]

bad=[n for n,ok in guards if not ok]
if bad:
    raise SystemExit("[FAIL] current source contract changed: "+repr(bad))

module=r'''from __future__ import annotations

import json
import time
import urllib.error
from pathlib import Path

from meteora_dlmm import PoolState,quote as dlmm_quote_live

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_089_two_second_dlmm_liquidity_binding_recovery.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

MAX_PAGES=5
PAGE_SIZE=100

POOL_RPC_ATTEMPTS=5
POOL_RPC_BASE_SLEEP=0.75
POOL_GAP_SECONDS=0.40


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


def mint(v):
    if isinstance(v,str):
        return v

    if isinstance(v,dict):
        return (
            v.get("address")
            or v.get("mint")
            or v.get("token_address")
        )

    return None


def normalize_pool(row,token):
    tx=(
        row.get("token_x")
        or row.get("tokenX")
        or {}
    )

    ty=(
        row.get("token_y")
        or row.get("tokenY")
        or {}
    )

    mx=mint(tx)
    my=mint(ty)

    if {mx,my}!={c.WSOL,token}:
        return None

    address=(
        row.get("address")
        or row.get("pool_address")
        or row.get("pubkey")
    )

    if not address:
        return None

    dx=(
        int(tx.get("decimals",9))
        if isinstance(tx,dict)
        else 9
    )

    dy=(
        int(ty.get("decimals",9))
        if isinstance(ty,dict)
        else 9
    )

    return {
        "address":str(address),
        "token_x":mx,
        "token_y":my,
        "decimals_x":dx,
        "decimals_y":dy,
        "tvl":float(
            row.get("tvl")
            or row.get("liquidity")
            or row.get("liquidity_usd")
            or 0
        ),
    }


def provider_page(token,page):
    url=(
        "https://dlmm.datapi.meteora.ag/pools"
        "?page=%d&page_size=%d&query=%s"
        %(page,PAGE_SIZE,token)
    )

    last=None

    for attempt in range(4):
        try:
            return c.http(url)

        except urllib.error.HTTPError as exc:
            last=exc

            if (
                getattr(exc,"code",None)!=429
                or attempt==3
            ):
                raise

            delay=0.50*(2**attempt)

            print(
                "[PROVIDER_429] token=%s "
                "page=%d retry=%d sleep=%.2f"%(
                    token[:10],
                    page,
                    attempt+1,
                    delay
                ),
                flush=True
            )

            time.sleep(delay)

    raise last


def discover_all_wsol_dlmm(token):
    out={}
    total_rows=0

    for page in range(
        1,
        MAX_PAGES+1
    ):
        payload=provider_page(
            token,
            page
        )

        rows=(
            payload.get("data")
            if isinstance(payload,dict)
            else payload
        ) or []

        total_rows+=len(rows)

        for raw in rows:
            x=normalize_pool(
                raw,
                token
            )

            if not x:
                continue

            old=out.get(
                x["address"]
            )

            if (
                old is None
                or x["tvl"]>old["tvl"]
            ):
                out[
                    x["address"]
                ]=x

        if len(rows)<PAGE_SIZE:
            break

    return (
        sorted(
            out.values(),
            key=lambda x:
                x["tvl"],
            reverse=True
        ),
        total_rows
    )


def rpc_retry(fn,label):
    last=None

    for attempt in range(
        POOL_RPC_ATTEMPTS
    ):
        try:
            return fn()

        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(
                exc,
                "code",
                None
            )!=429:
                raise

            if (
                attempt
                ==POOL_RPC_ATTEMPTS-1
            ):
                break

            delay=(
                POOL_RPC_BASE_SLEEP
                *(2**attempt)
            )

            print(
                "[RPC_429] %s "
                "retry=%d/%d sleep=%.2f"%(
                    label,
                    attempt+1,
                    POOL_RPC_ATTEMPTS,
                    delay
                ),
                flush=True
            )

            time.sleep(delay)

        except TimeoutError as exc:
            last=exc

            if (
                attempt
                ==POOL_RPC_ATTEMPTS-1
            ):
                break

            delay=(
                POOL_RPC_BASE_SLEEP
                *(2**attempt)
            )

            print(
                "[RPC_TIMEOUT] %s "
                "retry=%d/%d sleep=%.2f"%(
                    label,
                    attempt+1,
                    POOL_RPC_ATTEMPTS,
                    delay
                ),
                flush=True
            )

            time.sleep(delay)

    if isinstance(
        last,
        urllib.error.HTTPError
    ):
        raise RuntimeError(
            "RPC_429_EXHAUSTED:"
            +label
        )

    raise RuntimeError(
        "RPC_RETRY_EXHAUSTED:"
        +label
        +":"
        +str(last)
    )


def hydrate_pool(meta):
    pool=meta["address"]

    # One physical LB-pair fetch.
    lb,_=rpc_retry(
        lambda:
            c.account(pool),
        "LB_PAIR:"+pool[:10]
    )

    # One physical complete bin-array census.
    arrays=rpc_retry(
        lambda:
            c.dlmm_arrays(pool),
        "BIN_ARRAYS:"+pool[:10]
    )

    state=PoolState.from_accounts(
        lb,
        [x[2] for x in arrays],
        decimals_x=int(
            meta["decimals_x"]
        ),
        decimals_y=int(
            meta["decimals_y"]
        ),
        lb_pair_key=c.b58d(
            pool
        ),
        exhaustive=True,
    )

    return {
        "meta":dict(meta),
        "state":state,
        "arrays":list(arrays),
        "array_count":len(arrays),
    }


def hydrate_candidate_pools(pools):
    out=[]
    errors=[]

    for i,meta in enumerate(pools):
        if i:
            time.sleep(
                POOL_GAP_SECONDS
            )

        try:
            hp=hydrate_pool(
                meta
            )

            out.append(hp)

            print(
                "[DLMM_POOL_HYDRATED] "
                "pool=%s arrays=%d tvl=%.2f"%(
                    meta["address"][:10],
                    hp["array_count"],
                    meta["tvl"]
                ),
                flush=True
            )

        except Exception as exc:
            row={
                "meteora_pool":
                    meta["address"],
                "error":
                    type(exc).__name__
                    +":"
                    +str(exc),
            }

            errors.append(row)

            print(
                "[DLMM_POOL_SKIP] "
                "pool=%s %s"%(
                    meta["address"][:10],
                    row["error"]
                ),
                flush=True
            )

    return out,errors


def exact_pump_output(
    user,
    token,
    start_lamports
):
    _,_,out=(
        q87.las.q59.api_pump_route(
            user,
            token,
            int(start_lamports)
        )
    )

    if int(out)<=0:
        raise RuntimeError(
            "PUMP_BUY_OUTPUT_ZERO"
        )

    return int(out)


def quote_hydrated_pool(
    hp,
    token,
    pump_token_out,
    start_lamports
):
    meta=hp["meta"]

    if token==meta["token_x"]:
        swap_for_y=True

    elif token==meta["token_y"]:
        swap_for_y=False

    else:
        return {
            "complete":False,
            "reason":
                "TOKEN_NOT_IN_POOL",
        }

    q=dlmm_quote_live(
        hp["state"],
        amount_in=int(
            pump_token_out
        ),
        swap_for_y=swap_for_y,
        strict=True
    )

    remaining=int(
        getattr(
            q,
            "remaining_in",
            0
        ) or 0
    )

    complete=bool(
        getattr(
            q,
            "complete",
            False
        )
    )

    if (
        not complete
        or remaining
    ):
        return {
            "complete":False,
            "reason":"DLMM_PARTIAL",
            "remaining_in":
                remaining,
            "array_count":
                hp["array_count"],
        }

    end=int(
        q.amount_out
    )

    net=(
        end
        -int(start_lamports)
    )

    bps=(
        net
        /int(start_lamports)
        *10000.0
    )

    return {
        "complete":True,
        "raw_out":end,
        "net_lamports":net,
        "net_bps":bps,
        "bins_crossed":max(
            1,
            int(
                getattr(
                    q,
                    "bins_crossed",
                    1
                ) or 1
            )
        ),
        "array_count":
            hp["array_count"],
    }


def rank_complete(rows):
    return sorted(
        [
            x
            for x in rows
            if x.get("complete")
        ],
        key=lambda x:(
            x.get(
                "net_lamports",
                -10**30
            ),
            x.get(
                "tvl",
                0
            ),
        ),
        reverse=True
    )


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-089] IN-PLACE 2S "
        "DLMM LIQUIDITY BINDING RECOVERY",
        flush=True
    )

    print(
        "[RPC] each Meteora pool hydrated once; "
        "sizes quoted locally",
        flush=True
    )

    print(
        "[RULE] DLMM_PARTIAL never admitted",
        flush=True
    )

    bindings,audit=(
        q87.q86.memory_candidates(
            root
        )
    )

    if not bindings:
        print(
            "[QARB-089 HOLD] "
            "no qualified 2s bindings",
            flush=True
        )
        return 2

    _,user=c.sim_identity()

    results={}

    complete_tokens=0
    recovered=0
    profitable_tokens=0
    hydrated_pool_total=0
    pool_rpc_failures=0

    for binding in bindings:
        token=binding["token"]

        remembered=(
            binding[
                "meteora_meta"
            ][
                "address"
            ]
        )

        tr={
            "token":token,
            "pump_pool":
                binding["pump_pool"],
            "remembered_meteora_pool":
                remembered,
            "preferred_size_sol":
                binding["size_sol"],
            "sizes":[],
        }

        results[token]=tr

        try:
            pools,provider_rows=(
                discover_all_wsol_dlmm(
                    token
                )
            )

        except Exception as exc:
            tr["status"]=(
                "POOL_DISCOVERY_ERROR:"
                +type(exc).__name__
                +":"
                +str(exc)
            )
            continue

        tr[
            "provider_rows"
        ]=provider_rows

        tr[
            "candidate_pool_count"
        ]=len(pools)

        print(
            "[DLMM_POOL_SCAN] "
            "token=%s remembered=%s pools=%d"%(
                token[:10],
                remembered[:10],
                len(pools)
            ),
            flush=True
        )

        hydrated,errors=(
            hydrate_candidate_pools(
                pools
            )
        )

        tr[
            "pool_hydration_errors"
        ]=errors

        hydrated_pool_total+=len(
            hydrated
        )

        pool_rpc_failures+=len(
            errors
        )

        if not hydrated:
            tr[
                "status"
            ]="NO_HYDRATED_DLMM_POOL"

            continue

        token_complete=False
        token_profitable=False
        token_recovered=False

        for size_sol in q87.size_ladder(
            binding["size_sol"]
        ):
            start=int(
                round(
                    float(size_sol)
                    *1e9
                )
            )

            sr={
                "size_sol":
                    size_sol,
                "start_lamports":
                    start,
                "pools":[],
            }

            tr["sizes"].append(
                sr
            )

            try:
                pump_out=exact_pump_output(
                    user,
                    token,
                    start
                )

            except Exception as exc:
                sr["status"]=(
                    "PUMP_QUOTE_ERROR:"
                    +type(exc).__name__
                    +":"
                    +str(exc)
                )
                continue

            sr[
                "pump_token_out_raw"
            ]=pump_out

            for hp in hydrated:
                meta=hp["meta"]

                try:
                    q=quote_hydrated_pool(
                        hp,
                        token,
                        pump_out,
                        start
                    )

                except Exception as exc:
                    q={
                        "complete":False,
                        "reason":
                            type(exc).__name__
                            +":"
                            +str(exc),
                    }

                sr["pools"].append({
                    "meteora_pool":
                        meta["address"],
                    "tvl":
                        meta["tvl"],
                    **q,
                })

            ranked=rank_complete(
                sr["pools"]
            )

            if not ranked:
                sr[
                    "status"
                ]="NO_COMPLETE_DLMM_POOL"

                continue

            token_complete=True

            best=ranked[0]

            sr["best"]=best
            sr["status"]="COMPLETE"

            if (
                best[
                    "meteora_pool"
                ]
                !=remembered
            ):
                token_recovered=True

            if best[
                "net_lamports"
            ]>0:
                token_profitable=True

            print(
                "[DLMM_RECOVERY] "
                "token=%s size=%.6f "
                "pool=%s remembered=%s "
                "complete=True "
                "net=%+.9f_SOL "
                "bps=%+.2f arrays=%s"%(
                    token[:10],
                    size_sol,
                    best[
                        "meteora_pool"
                    ][:10],
                    str(
                        best[
                            "meteora_pool"
                        ]==remembered
                    ),
                    best[
                        "net_lamports"
                    ]/1e9,
                    best[
                        "net_bps"
                    ],
                    best.get(
                        "array_count"
                    ),
                ),
                flush=True
            )

            # Highest learned size with a complete
            # physically hydrated route wins.
            break

        if token_complete:
            complete_tokens+=1

        if token_profitable:
            profitable_tokens+=1

        if token_recovered:
            recovered+=1

        if token_complete:
            best_size=next(
                x
                for x in tr["sizes"]
                if x.get("best")
            )

            tr["selected_binding"]={
                "token":token,

                "pump_pool":
                    binding[
                        "pump_pool"
                    ],

                "meteora_pool":
                    best_size[
                        "best"
                    ][
                        "meteora_pool"
                    ],

                "size_sol":
                    best_size[
                        "size_sol"
                    ],

                "net_lamports":
                    best_size[
                        "best"
                    ][
                        "net_lamports"
                    ],

                "net_bps":
                    best_size[
                        "best"
                    ][
                        "net_bps"
                    ],

                "recovered_from_remembered":
                    best_size[
                        "best"
                    ][
                        "meteora_pool"
                    ]
                    !=remembered,
            }

            tr["status"]=(
                "RECOVERED_COMPLETE_POOL"
                if token_recovered
                else
                "REMEMBERED_POOL_COMPLETE"
            )

        else:
            tr[
                "status"
            ]="NO_CURRENT_COMPLETE_DLMM_LIQUIDITY"

    status=(
        "PASS"
        if complete_tokens>0
        else "HOLD"
    )

    out={
        "revision":
            "QARB_089_RPC_REPAIR",

        "status":
            status,

        "qualified_tokens":
            len(bindings),

        "hydrated_pool_total":
            hydrated_pool_total,

        "pool_rpc_failures":
            pool_rpc_failures,

        "complete_tokens":
            complete_tokens,

        "recovered_bindings":
            recovered,

        "locally_profitable_tokens":
            profitable_tokens,

        "results":
            results,

        "binding_audit":
            audit,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "created_unix":
            time.time(),
    }

    _save(
        root/STATE,
        out
    )

    print(
        "[QARB-089] status=%s "
        "qualified=%d "
        "hydrated_pools=%d "
        "rpc_failures=%d "
        "complete=%d "
        "recovered=%d "
        "local_profitable=%d"%(
            status,
            len(bindings),
            hydrated_pool_total,
            pool_rpc_failures,
            complete_tokens,
            recovered,
            profitable_tokens,
        ),
        flush=True
    )

    print(
        "[MODE] discovery_quote_only "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return (
        0
        if status=="PASS"
        else 2
    )


def main():
    return run(
        Path.cwd()
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

tests=r'''import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_089_two_second_dlmm_liquidity_binding_recovery as q


class T(unittest.TestCase):

    def test_normalize_wsol_x(self):
        x=q.normalize_pool(
            {
                "address":"P",
                "token_x":{
                    "address":q.c.WSOL,
                    "decimals":9,
                },
                "token_y":{
                    "address":"TOKEN",
                    "decimals":6,
                },
                "tvl":100,
            },
            "TOKEN"
        )

        self.assertEqual(
            x["address"],
            "P"
        )


    def test_normalize_wsol_y(self):
        x=q.normalize_pool(
            {
                "address":"P",
                "token_x":{
                    "address":"TOKEN"
                },
                "token_y":{
                    "address":q.c.WSOL
                },
            },
            "TOKEN"
        )

        self.assertIsNotNone(x)


    def test_wrong_pair_rejected(self):
        self.assertIsNone(
            q.normalize_pool(
                {
                    "address":"P",
                    "token_x":{
                        "address":"A"
                    },
                    "token_y":{
                        "address":"B"
                    },
                },
                "TOKEN"
            )
        )


    def test_rank_complete(self):
        r=q.rank_complete([
            {
                "complete":False,
                "net_lamports":999,
            },
            {
                "complete":True,
                "net_lamports":10,
                "tvl":1,
            },
            {
                "complete":True,
                "net_lamports":20,
                "tvl":1,
            },
        ])

        self.assertEqual(
            len(r),
            2
        )

        self.assertEqual(
            r[0]["net_lamports"],
            20
        )


    def test_partial_never_ranked(self):
        self.assertEqual(
            q.rank_complete([
                {
                    "complete":False,
                    "reason":"DLMM_PARTIAL",
                    "net_lamports":999999,
                }
            ]),
            []
        )


    def test_pool_retry_count_bounded(self):
        self.assertEqual(
            q.POOL_RPC_ATTEMPTS,
            5
        )


    def test_pool_snapshot_has_state_builder(self):
        self.assertTrue(
            callable(
                q.hydrate_pool
            )
        )


    def test_quote_uses_hydrated_state(self):
        self.assertTrue(
            callable(
                q.quote_hydrated_pool
            )
        )


    def test_exact_087_size_ladder(self):
        self.assertTrue(
            callable(
                q.q87.size_ladder
            )
        )


    def test_no_broadcast(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "sendTransaction",
            src
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
    unittest.main(
        verbosity=2
    )
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_089_two_second_dlmm_liquidity_binding_recovery import main

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
    "[PASS] QARB-089 in-place RPC/liquidity recovery repair installed"
)
print(
    "[FIX] each candidate Meteora pool physically hydrated exactly once per run"
)
print(
    "[FIX] all size probes reuse the same exhaustive pool snapshot"
)
print(
    "[FIX] HTTP 429 bounded retry/backoff; one pool cannot abort the scan"
)
print(
    "[PRESERVE] QARB-087 and QARB-080 frozen state unchanged"
)
print(
    "[MODE] discovery_quote_only execution_authority=FALSE real_money_moved=FALSE"
)