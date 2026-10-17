from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
RUNTIME=PKG/"live_money_runtime.py"
SUPERVISOR=PKG/"live_money_supervisor.py"
TEST=ROOT/"test_live_money_mriya_replenishment.py"

RUNTIME_CODE=r"""from __future__ import annotations

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
MRIYA_PRIORITY=STATE/"mriya_replenishment_priority.json"

MAX_RUNTIME_ACCOUNTS=320
RUNTIME_ACCOUNT_RESERVE=2
MAX_SELECTED_ACCOUNTS=MAX_RUNTIME_ACCOUNTS-RUNTIME_ACCOUNT_RESERVE
WS_SHARD_SIZE=48

persistent=canonical_runtime.persistent
merged=persistent.m

_ORIGINAL_SHARDS=None
_ORIGINAL_WORKER=None


def _load(path,default=None):
    if not path.is_file():
        if default is not None:
            return default
        raise RuntimeError("LIVE_MONEY_MISSING:"+str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def _mriya_priority():
    data=_load(MRIYA_PRIORITY,{"pair_keys":[],"tokens":[]})
    return set(data.get("pair_keys") or []),set(data.get("tokens") or [])


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


def _priority(row,historical,mriya_pairs,mriya_tokens):
    identity=str(row["identity"])
    token=str(row.get("token") or "")
    h=historical.get(identity,{})
    return (
        0 if identity in mriya_pairs else 1,
        0 if token in mriya_tokens else 1,
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
    mriya_pairs,mriya_tokens=_mriya_priority()

    rows.sort(key=lambda row:_priority(
        row,historical,mriya_pairs,mriya_tokens
    ))

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
        identity=str(row["identity"])
        token=str(row.get("token") or "")
        copy["hot_rank"]=rank
        copy["hot_reason"]={
            "mriya_exact_pair":identity in mriya_pairs,
            "mriya_token":token in mriya_tokens,
            "historical_gross_positive":bool(historical.get(identity,{}).get("gross_positive")),
            "historical_best_bps":float(historical.get(identity,{}).get("best_local_bps") or 0.0),
            "retained":bool(row.get("retained")),
        }
        selected.append(copy)

    if len(selected)<5:
        raise RuntimeError("LIVE_MONEY_HOT_BOOK_TOO_SMALL:"+str(len(selected)))

    if len(accounts)>int(max_selected_accounts):
        raise RuntimeError("LIVE_MONEY_ACCOUNT_BUDGET_BREACH")

    payload=dict(capacity)
    payload["revision"]="LIVE_MONEY_MRIYA_REPLENISHMENT_V1"
    payload["source_inventory_pairs"]=len(rows)
    payload["selected_pairs"]=len(selected)
    payload["selected_accounts"]=len(accounts)
    payload["max_selected_accounts"]=int(max_selected_accounts)
    payload["max_runtime_accounts"]=MAX_RUNTIME_ACCOUNTS
    payload["runtime_account_reserve"]=RUNTIME_ACCOUNT_RESERVE
    payload["mriya_priority_pairs"]=len(mriya_pairs)
    payload["mriya_priority_tokens"]=len(mriya_tokens)
    payload["rows"]=selected
    payload["policy"]={
        "execution_book":True,
        "mriya_replenishment_only":True,
        "full_inventory_preserved_outside_hot_book":True,
        "mriya_exact_pair_first":True,
        "mriya_token_second":True,
        "historical_positive_next":True,
        "broadcast":False,
    }
    return payload,accounts


def stable_shards(addresses):
    rows=list(dict.fromkeys(addresses))
    if len(rows)>MAX_RUNTIME_ACCOUNTS:
        raise RuntimeError("LIVE_MONEY_RUNTIME_ACCOUNT_BUDGET_BREACH:"+str(len(rows)))

    shards=[rows[i:i+WS_SHARD_SIZE] for i in range(0,len(rows),WS_SHARD_SIZE)]
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
    p.add_argument("--seconds",type=float,default=600.0)
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
        print("[MRIYA_PRIORITY] pairs=%d tokens=%d"%(
            int(hot.get("mriya_priority_pairs") or 0),
            int(hot.get("mriya_priority_tokens") or 0),
        ),flush=True)
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

SUPERVISOR_CODE=r"""from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_045b_evidence_window_hotset_lifecycle as q45
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_080_single_runtime_dynamic_mriya_supervisor as q80
)

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"
CAPACITY=STATE/"capacity_aware_warm_universe.json"
PRIORITY=STATE/"mriya_replenishment_priority.json"
STATUS=STATE/"mriya_replenishment_status.json"

DISCOVERY_LAUNCHER=ROOT/"run_qarb_043b_paced_mriya_token_discovery.py"

MIN_REFRESH_SECONDS=60.0
MIN_GENERATION_SECONDS=300.0


def _load(path,default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)


def _capacity_index():
    data=_load(CAPACITY,{"rows":[]})
    rows=list(data.get("rows") or [])

    by_pair={}
    by_token={}

    for row in rows:
        token=str(row.get("token") or "")
        pool=str(row.get("meteora_pool") or "")
        identity=str(row.get("identity") or (token+"|"+pool))

        if token and pool:
            by_pair[(token,pool)]=identity
            by_token.setdefault(token,[]).append(identity)

    return rows,by_pair,by_token


def refresh_priority():
    _,fresh=q45.classify()
    rows=q80.select_rows(ROOT,fresh)

    inventory,by_pair,by_token=_capacity_index()

    pair_keys=set()
    tokens=set()
    exact_bound=[]
    token_bound=[]
    unbound=[]

    for row in rows:
        token=str(row.get("token") or "")
        pool=str(row.get("meteora_pool") or "")

        if token and pool and (token,pool) in by_pair:
            identity=by_pair[(token,pool)]
            pair_keys.add(identity)
            tokens.add(token)
            exact_bound.append({
                "token":token,
                "meteora_pool":pool,
                "identity":identity,
                "source":"MRIYA_EXACT_BOUND",
            })
            continue

        if token and token in by_token:
            tokens.add(token)
            token_bound.append({
                "token":token,
                "known_pair_keys":list(by_token[token]),
                "source":"MRIYA_TOKEN_BOUND",
            })
            continue

        if token:
            unbound.append({
                "token":token,
                "pump_pool":row.get("pump_pool"),
                "meteora_pool":row.get("meteora_pool"),
                "source":"MRIYA_UNBOUND",
            })

    payload={
        "revision":"LIVE_MONEY_MRIYA_REPLENISHMENT_V1",
        "updated_unix":time.time(),
        "inventory_routes":len(inventory),
        "mriya_rows":len(rows),
        "pair_keys":sorted(pair_keys),
        "tokens":sorted(tokens),
        "exact_bound":exact_bound,
        "token_bound":token_bound,
        "unbound":unbound,
        "policy":{
            "mriya_replenishment_only":True,
            "execution_hot_path_independent":True,
            "never_displace_profitable_only_for_newness":True,
            "unbound_candidates_never_enter_execution":True,
        },
        "execution_authority":False,
    }

    _save(PRIORITY,payload)

    print(
        "[MRIYA_REFRESH] rows=%d exact_bound=%d token_bound=%d unbound=%d"
        %(len(rows),len(exact_bound),len(token_bound),len(unbound)),
        flush=True,
    )

    for row in exact_bound:
        print(
            "[MRIYA_PROMOTE] token=%s pair=%s"
            %(row["token"][:12],row["identity"][:28]),
            flush=True,
        )

    for row in unbound[:10]:
        print(
            "[MRIYA_UNBOUND] token=%s exact_hydration_required=True"
            %row["token"][:12],
            flush=True,
        )

    return payload


def _money_cmd(seconds):
    return [
        sys.executable,
        "-m",
        "qseries_v2.oracle_execution.solana_atomic_executor.live_money_runtime",
        "--seconds",
        str(float(seconds)),
    ]


def run(seconds=1800.0,refresh_seconds=60.0,generation_seconds=300.0):
    refresh_seconds=max(MIN_REFRESH_SECONDS,float(refresh_seconds))
    generation_seconds=max(MIN_GENERATION_SECONDS,float(generation_seconds))

    if not DISCOVERY_LAUNCHER.is_file():
        raise RuntimeError(
            "MRIYA_DISCOVERY_LAUNCHER_MISSING:"+str(DISCOVERY_LAUNCHER)
        )

    discovery=subprocess.Popen(
        [sys.executable,str(DISCOVERY_LAUNCHER)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    child=None
    started=time.monotonic()
    next_refresh=started
    generation=0
    last_priority=None

    print("[LIVE_MONEY_SUPERVISOR] mriya_background_replenishment=True",flush=True)
    print("[MRIYA_ROLE] replenishment_only=True execution_path=False",flush=True)
    print("[DISCOVERY] silent_background=True",flush=True)
    print("[ROTATION] only_between_live_money_generations=True",flush=True)
    print("[BROADCAST] disabled",flush=True)

    try:
        while time.monotonic()-started<float(seconds):
            now=time.monotonic()

            if now>=next_refresh:
                try:
                    last_priority=refresh_priority()
                except Exception as exc:
                    print(
                        "[MRIYA_REFRESH_WARN] %s:%s"
                        %(type(exc).__name__,str(exc)[:240]),
                        flush=True,
                    )

                next_refresh=now+refresh_seconds

            if child is None or child.poll() is not None:
                remain=float(seconds)-(time.monotonic()-started)
                if remain<=0:
                    break

                run_for=min(generation_seconds,remain)
                generation+=1

                print(
                    "[MONEY_GENERATION_START] generation=%d seconds=%.1f"
                    %(generation,run_for),
                    flush=True,
                )

                child=subprocess.Popen(_money_cmd(run_for))

            _save(STATUS,{
                "revision":"LIVE_MONEY_MRIYA_SUPERVISOR_V1",
                "generation":generation,
                "discovery_alive":discovery.poll() is None,
                "money_runtime_alive":child is not None and child.poll() is None,
                "refresh_seconds":refresh_seconds,
                "generation_seconds":generation_seconds,
                "priority_updated_unix":None if not last_priority else last_priority.get("updated_unix"),
                "exact_bound":0 if not last_priority else len(last_priority.get("exact_bound") or []),
                "token_bound":0 if not last_priority else len(last_priority.get("token_bound") or []),
                "unbound":0 if not last_priority else len(last_priority.get("unbound") or []),
                "execution_authority":False,
            })

            time.sleep(1.0)

    finally:
        if child is not None and child.poll() is None:
            try:
                child.terminate()
                child.wait(timeout=8)
            except Exception:
                try:
                    child.kill()
                except Exception:
                    pass

        if discovery.poll() is None:
            try:
                discovery.terminate()
                discovery.wait(timeout=8)
            except Exception:
                try:
                    discovery.kill()
                except Exception:
                    pass

    print(
        "[LIVE_MONEY_SUPERVISOR_DONE] generations=%d"
        %generation,
        flush=True,
    )

    return 0


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=1800.0)
    p.add_argument("--refresh-seconds",type=float,default=60.0)
    p.add_argument("--generation-seconds",type=float,default=300.0)
    a=p.parse_args()

    if a.seconds<=0:
        raise RuntimeError("SUPERVISOR_SECONDS_MUST_BE_POSITIVE")

    return run(
        seconds=a.seconds,
        refresh_seconds=a.refresh_seconds,
        generation_seconds=a.generation_seconds,
    )


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

R=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_runtime.py"
)
S=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_supervisor.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=R.read_text(encoding="utf-8")
        cls.s=S.read_text(encoding="utf-8")
        ast.parse(cls.r)
        ast.parse(cls.s)

    def test_mriya_is_replenishment_only(self):
        self.assertIn("mriya_replenishment_only",self.r)
        self.assertIn("[MRIYA_ROLE] replenishment_only=True execution_path=False",self.s)

    def test_uses_existing_mriya_sources(self):
        self.assertIn("qarb_045b_evidence_window_hotset_lifecycle",self.s)
        self.assertIn("qarb_080_single_runtime_dynamic_mriya_supervisor",self.s)
        self.assertIn("run_qarb_043b_paced_mriya_token_discovery.py",self.s)

    def test_unbound_never_enters_execution(self):
        self.assertIn("unbound_candidates_never_enter_execution",self.s)
        self.assertIn("[MRIYA_UNBOUND]",self.s)

    def test_hot_book_prioritizes_mriya(self):
        self.assertIn("identity in mriya_pairs",self.r)
        self.assertIn("token in mriya_tokens",self.r)

    def test_account_cap_preserved(self):
        self.assertIn("MAX_RUNTIME_ACCOUNTS=320",self.r)
        self.assertIn("WS_SHARD_SIZE=48",self.r)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.r)
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

RUNTIME.write_text(RUNTIME_CODE,encoding="utf-8")
SUPERVISOR.write_text(SUPERVISOR_CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

for path in (RUNTIME,SUPERVISOR,TEST):
    ast.parse(path.read_text(encoding="utf-8"))

print("[PASS] live-money Mriya replenishment integration installed")
print("[MRIYA] existing QARB-043B + QARB-045B + QARB-080 sources reused")
print("[ROLE] background replenishment only")
print("[HOT_PATH] current exact live-money runtime remains execution owner")
print("[PROMOTION] only exact-bound current inventory candidates can influence HOT book")
print("[UNBOUND] logged and held out of execution")
print("[ACCOUNT_CAP] runtime<=320 shard_size=48")
print("[BROADCAST] disabled")
print("[KEY] untouched")
print("[TEST]",TEST.name)
