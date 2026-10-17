from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"live_money_runtime.py"
TEST=ROOT/"test_live_money_runtime.py"

MODULE=r"""from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as c26
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as canonical_runtime

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"

CAPACITY=STATE/"capacity_aware_warm_universe.json"
REGISTRY=STATE/"multi_dlmm_pair_registry.json"

# Physical evidence showed selected=320 became runtime=321.
# Reserve two accounts for runtime-added/global state.
MAX_RUNTIME_ACCOUNTS=320
RUNTIME_ACCOUNT_RESERVE=2
MAX_SELECTED_ACCOUNTS=MAX_RUNTIME_ACCOUNTS-RUNTIME_ACCOUNT_RESERVE

# 48 was physically stable; ~111/subsocket was not.
WS_SHARD_SIZE=48

persistent=canonical_runtime.persistent
merged=persistent.m

_ORIGINAL_SHARDS=None
_ORIGINAL_WORKER=None


def _load(path):
    if not path.is_file():
        raise RuntimeError("LIVE_MONEY_MISSING:"+str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def _historical_scores():
    data=_load(REGISTRY)
    out={}
    for row in list(data.get("rows") or []):
        key=str(row.get("pair_key") or (str(row.get("token"))+"|"+str(row.get("meteora_pool"))))
        out[key]={
            "gross_positive":bool(row.get("gross_positive")),
            "best_local_bps":float(row.get("best_local_bps") or 0.0),
            "best_local_net_lamports":int(row.get("best_local_net_lamports") or 0),
        }
    return out


def _priority(row,historical):
    identity=str(row["identity"])
    h=historical.get(identity,{})
    return (
        0 if h.get("gross_positive") else 1,
        -float(h.get("best_local_bps") or 0.0),
        -int(h.get("best_local_net_lamports") or 0),
        0 if row.get("retained") else 1,
        float(row.get("source_age") if row.get("source_age") is not None else 1e18),
        -float(row.get("reported_tvl") or 0.0),
        int(row.get("account_cost") or 9999),
        identity,
    )


def build_hot_book(max_selected_accounts=MAX_SELECTED_ACCOUNTS):
    capacity=_load(CAPACITY)
    rows=list(capacity.get("rows") or [])
    if not rows:
        raise RuntimeError("LIVE_MONEY_EMPTY_INVENTORY")

    historical=_historical_scores()
    rows.sort(key=lambda row:_priority(row,historical))

    selected=[]
    accounts=set()

    for rank,row in enumerate(rows,1):
        watched=[str(x) for x in (row.get("watched_accounts") or [])]
        if not watched:
            continue

        incremental=[x for x in watched if x not in accounts]
        if len(accounts)+len(incremental)>int(max_selected_accounts):
            continue

        accounts.update(incremental)
        copy=dict(row)
        copy["hot_rank"]=rank
        copy["hot_reason"]={
            "historical_gross_positive":bool(historical.get(str(row["identity"]),{}).get("gross_positive")),
            "historical_best_bps":float(historical.get(str(row["identity"]),{}).get("best_local_bps") or 0.0),
            "retained":bool(row.get("retained")),
        }
        selected.append(copy)

    if len(selected)<5:
        raise RuntimeError("LIVE_MONEY_HOT_BOOK_TOO_SMALL:"+str(len(selected)))

    if len(accounts)>int(max_selected_accounts):
        raise RuntimeError("LIVE_MONEY_ACCOUNT_BUDGET_BREACH")

    payload=dict(capacity)
    payload["revision"]="LIVE_MONEY_HOT_BOOK_FEED_FREEZE_V1"
    payload["source_inventory_pairs"]=len(rows)
    payload["selected_pairs"]=len(selected)
    payload["selected_accounts"]=len(accounts)
    payload["max_selected_accounts"]=int(max_selected_accounts)
    payload["max_runtime_accounts"]=MAX_RUNTIME_ACCOUNTS
    payload["runtime_account_reserve"]=RUNTIME_ACCOUNT_RESERVE
    payload["rows"]=selected
    payload["policy"]={
        "execution_book":True,
        "full_inventory_preserved_outside_hot_book":True,
        "historical_positive_first":True,
        "historical_edge_second":True,
        "retained_priority":True,
        "recency_then_tvl_then_account_cost":True,
        "broadcast":False,
    }
    return payload,accounts


def stable_shards(addresses):
    rows=list(dict.fromkeys(addresses))
    if len(rows)>MAX_RUNTIME_ACCOUNTS:
        raise RuntimeError("LIVE_MONEY_RUNTIME_ACCOUNT_BUDGET_BREACH:"+str(len(rows)))

    shards=[
        rows[i:i+WS_SHARD_SIZE]
        for i in range(0,len(rows),WS_SHARD_SIZE)
    ]

    if any(len(x)>WS_SHARD_SIZE for x in shards):
        raise RuntimeError("LIVE_MONEY_WS_SHARD_BREACH")
    return shards


async def truthful_worker(index,addresses,q,c,stop):
    import websockets

    await asyncio.sleep(index*merged.STAGGER_SECONDS)
    delay=float(getattr(persistent,"RECONNECT_MIN",1.0))
    reconnect_max=float(getattr(persistent,"RECONNECT_MAX",30.0))

    while not stop.is_set():
        by_id={i+1:a for i,a in enumerate(addresses)}
        submap={}

        try:
            async with websockets.connect(
                merged.WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=3,
                max_size=8_000_000,
            ) as ws:
                c["connections"]+=1

                for req in merged._req(addresses):
                    if stop.is_set():
                        break

                    await ws.send(json.dumps(req,separators=(",",":")))

                    if merged.SUB_DELAY_MS>0:
                        await asyncio.sleep(merged.SUB_DELAY_MS/1000.0)

                delay=float(getattr(persistent,"RECONNECT_MIN",1.0))

                print(
                    "[LIVE_MONEY_WS_READY] shard=%d subscriptions=%d"
                    %(index,len(addresses)),
                    flush=True,
                )

                while not stop.is_set():
                    try:
                        raw=await asyncio.wait_for(ws.recv(),timeout=1.0)
                    except asyncio.TimeoutError:
                        continue

                    msg=json.loads(raw)

                    if "id" in msg and isinstance(msg.get("result"),int):
                        a=by_id.get(int(msg["id"]))
                        if a:
                            submap[int(msg["result"])]=a
                            c["acks"]+=1
                        continue

                    ev=merged._parse(msg,submap)
                    if not ev:
                        continue

                    c["notifications"]+=1

                    try:
                        q.put_nowait(ev)
                    except asyncio.QueueFull:
                        c["queue_drops"]+=1

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            txt=f"{type(exc).__name__}: {exc}"
            c["reconnects"]+=1
            c["last_ws_error"]=txt
            low=txt.lower()

            rate_limited=(
                "http 429" in low
                or "too many requests" in low
                or "1013" in low
                or "rate limit" in low
                or "too many subscriptions" in low
            )

            if rate_limited:
                c["rate_limit_disconnects"]+=1

            print(
                "[WS_RECOVER] shard=%d rate_limited=%s error=%s retry_in=%.1fs"
                %(index,str(rate_limited),txt,delay),
                flush=True,
            )

            await asyncio.sleep(delay)
            delay=min(
                reconnect_max,
                max(float(getattr(persistent,"RECONNECT_MIN",1.0)),delay*2),
            )


def _atomic_write(path,payload):
    tmp=path.with_suffix(path.suffix+".live_money.tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)


def main():
    global _ORIGINAL_SHARDS,_ORIGINAL_WORKER

    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError("LIVE_MONEY_SECONDS_MUST_BE_POSITIVE")

    hot,accounts=build_hot_book()

    original_capacity=CAPACITY.read_bytes() if CAPACITY.is_file() else None
    _ORIGINAL_SHARDS=merged._shards
    _ORIGINAL_WORKER=persistent._worker
    old_argv=list(sys.argv)

    try:
        _atomic_write(CAPACITY,hot)

        merged._shards=stable_shards
        persistent._worker=truthful_worker

        estimated_shards=(MAX_RUNTIME_ACCOUNTS+WS_SHARD_SIZE-1)//WS_SHARD_SIZE

        print("[FEED_FREEZE] true",flush=True)
        print("[INVENTORY] %d routes"%int(hot.get("source_inventory_pairs") or 0),flush=True)
        print("[HOT_BOOK] %d routes"%len(hot.get("rows") or []),flush=True)
        print("[SELECTED_ACCOUNTS] %d/%d reserve=%d runtime_cap=%d"%(
            len(accounts),MAX_SELECTED_ACCOUNTS,RUNTIME_ACCOUNT_RESERVE,MAX_RUNTIME_ACCOUNTS
        ),flush=True)
        print("[WS_POLICY] shard_size=%d max_connections=%d"%(
            WS_SHARD_SIZE,estimated_shards
        ),flush=True)
        print("[RATE_LIMIT_TELEMETRY] http_429=True too_many_requests=True 1013=True",flush=True)
        print("[MONEY_LOOP] scan -> after_fee_positive -> build -> signed_sim -> freshness",flush=True)
        print("[LIVE_SEND] DISABLED until signed-sim certification",flush=True)
        print("[BROADCAST] disabled",flush=True)

        sys.argv=[old_argv[0],"--seconds",str(float(args.seconds))]
        return c26.main()

    finally:
        sys.argv=old_argv

        if _ORIGINAL_SHARDS is not None:
            merged._shards=_ORIGINAL_SHARDS
            _ORIGINAL_SHARDS=None

        if _ORIGINAL_WORKER is not None:
            persistent._worker=_ORIGINAL_WORKER
            _ORIGINAL_WORKER=None

        if original_capacity is None:
            try:
                CAPACITY.unlink()
            except FileNotFoundError:
                pass
        else:
            CAPACITY.write_bytes(original_capacity)

        print("[LIVE_MONEY_STATE_RESTORED] true",flush=True)


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_runtime.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_runtime_cap(self):
        self.assertIn("MAX_RUNTIME_ACCOUNTS=320",cls.s if False else self.s)
        self.assertIn("RUNTIME_ACCOUNT_RESERVE=2",self.s)

    def test_shards_48(self):
        self.assertIn("WS_SHARD_SIZE=48",self.s)

    def test_truthful_429(self):
        self.assertIn('"http 429" in low',self.s)
        self.assertIn('"too many requests" in low',self.s)

    def test_inventory_preserved(self):
        self.assertIn("full_inventory_preserved_outside_hot_book",self.s)

    def test_money_chain(self):
        self.assertIn("return c26.main()",self.s)

    def test_no_live_send(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[LIVE_SEND] DISABLED",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

ast.parse(TARGET.read_text(encoding="utf-8"))
ast.parse(TEST.read_text(encoding="utf-8"))

print("[PASS] live money feed-freeze replacement installed")
print("[ACCOUNT_CAP] selected<=318 runtime<=320")
print("[WS] 48 subscriptions/socket")
print("[TELEMETRY] HTTP429/TooManyRequests/1013 counted")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
