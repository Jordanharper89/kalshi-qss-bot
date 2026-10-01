from __future__ import annotations
import asyncio,json,os,subprocess,sys,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_045b_evidence_window_hotset_lifecycle as q45
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_047b_paced_dynamic_hotset_supervisor as q47
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q72
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q73

STATE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_single_runtime_state.json")
SEEN=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_seen_tokens.json")
MEMORY=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_binding_memory.json")
PRESENCE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_presence.json")
HYDRATION_LOCK=Path("runtime_state/qseries/qarb_execution_engineering/qarb_080_hydration.lock")

MIN_REFRESH_SECONDS=60.0
MAX_HORIZON_SECONDS=90.0
DRAIN_TAIL_SECONDS=95.0
LOCK_STALE_SECONDS=240.0
WS_CONNECTION_STAGGER_SECONDS=2.0

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

def _load(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def lifecycle_sets(root):
    learned=q70._load(root).get("tokens",{})
    life=q72.run(root).get("tokens",{})
    active={t for t,x in learned.items() if x.get("status")=="ACTIVE"}
    retired={t for t,x in life.items() if x.get("lifecycle")=="RETIRED"}
    return active,retired

def select_rows(root,fresh):
    root=Path(root)
    active,retired=lifecycle_sets(root)
    mem=dict(_load(root/MEMORY,{"rows":{}}).get("rows",{}))

    for x in fresh:
        if x.get("token"):
            mem[x["token"]]=x

    selected={x["token"]:x for x in fresh if x.get("token")}

    for token in sorted(active-retired):
        if token in mem:
            selected.setdefault(token,mem[token])

    _save(root/MEMORY,{"rows":mem})
    return list(selected.values())

def announce(root,rows):
    root=Path(root)
    seen=set(_load(root/SEEN,{"tokens":[]}).get("tokens",[]))
    prior=set(_load(root/PRESENCE,{"tokens":[]}).get("tokens",[]))
    _,retired=lifecycle_sets(root)
    now={x["token"] for x in rows if x.get("token")}

    entered=now-prior
    introduced=sorted(entered-seen)
    returned=sorted(entered&seen&retired)

    for token in introduced:
        print("[NEW_TOKEN] token=%s"%token,flush=True)

    for token in returned:
        print("[TOKEN_RETURN] token=%s prior=RETIRED"%token,flush=True)

    _save(root/SEEN,{"tokens":sorted(seen|now)})
    _save(root/PRESENCE,{"tokens":sorted(now)})
    return introduced,returned

def _lock_path(root):
    return Path(root)/HYDRATION_LOCK

def acquire_hydration_lock(root,generation):
    p=_lock_path(root)
    p.parent.mkdir(parents=True,exist_ok=True)

    while True:
        try:
            fd=os.open(
                str(p),
                os.O_CREAT|os.O_EXCL|os.O_WRONLY
            )

            os.write(
                fd,
                ("%d,%d,%.6f"%(
                    os.getpid(),
                    generation,
                    time.time()
                )).encode()
            )

            os.close(fd)
            return p

        except FileExistsError:
            try:
                if time.time()-p.stat().st_mtime>LOCK_STALE_SECONDS:
                    p.unlink(missing_ok=True)
                    continue

            except FileNotFoundError:
                continue

            time.sleep(.25)

def release_hydration_lock(path):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass

class LearningAgeLane(q47.AgeDrainLane):
    def capture(self,row):
        super().capture(row)

        x=q73.observe(
            self.root,
            row
        )

        print(
            "[ACTIVE_PROFIT] token=%s status=%s samples=%d wins=%d pnl=%+.9f_SOL"%(
                row["token"][:10],
                x["status"],
                x["samples"],
                x["wins"],
                x["pnl_sol"]
            ),
            flush=True
        )

async def generation_worker(
    bindings,
    seconds,
    admit_seconds,
    generation
):
    root=Path.cwd()

    d=json.loads(
        Path(bindings).read_text(
            encoding="utf-8"
        )
    )

    meta={
        x["token"]:x.get("lifecycle",{})
        for x in d.get("rows",[])
    }

    q61d.CONNECTION_STAGGER_SECONDS=WS_CONNECTION_STAGGER_SECONDS
    q61d.install()

    q47.p.m._shards=q61d.capped_valves
    q47.p._worker=q61d.staggered_worker

    # Apply exact existing QARB-061A serialized HTTP valve
    # before this generation performs its one warm hydration.
    q47.p.m.pd.c.rpc=rv.gated_rpc

    lock=acquire_hydration_lock(
        root,
        generation
    )

    try:
        pairs,landing=q47.prepare_from(
            bindings,
            root
        )
    finally:
        release_hydration_lock(lock)

    # The expensive HTTP warm-up happened exactly once.
    # persistent_profit_runtime will reuse this hydrated state.
    def cached_prepare(_root):
        return pairs,landing

    qg.VENUE_TS.clear()

    q47.p.m.pd.prepare_pairs=cached_prepare
    q47.p.m.pd.apply_account_event=qg.tracked_apply

    class Lane(LearningAgeLane):
        def __init__(self,root,state):
            super().__init__(
                root,
                state,
                meta,
                admit_seconds,
                generation
            )

    q47.p.SimulationLane=Lane

    print(
        "[GENERATION_START] gen=%s active=%d admit=%.1fs drain_until=%.1fs"%(
            generation,
            len(meta),
            admit_seconds,
            seconds
        ),
        flush=True
    )

    print(
        "[HYDRATION] gen=%s pairs=%d serialized=True rpc_gap=%.2fs rpc_calls=%d caught_429=%d"%(
            generation,
            len(pairs),
            rv.MIN_RPC_GAP_SECONDS,
            rv.RPC_CALLS,
            rv.RPC_429
        ),
        flush=True
    )

    result=await q47.p.serve(
        root,
        seconds
    )

    reconnects=int(result.get("reconnects",0)) if isinstance(result,dict) else 0
    rate_limits=int(result.get("rate_limit_disconnects",0)) if isinstance(result,dict) else 0
    clean=(reconnects==0 and rate_limits==0)

    print(
        "[WS_TRANSPORT_%s] gen=%d reconnects=%d rate_limits=%d stagger=%.2fs"%(
            "PASS" if clean else "HOLD",
            generation,
            reconnects,
            rate_limits,
            WS_CONNECTION_STAGGER_SECONDS
        ),
        flush=True
    )

    return 0 if clean else 2

def worker_cmd(
    path,
    generation,
    drain_seconds,
    admit_seconds
):
    return [
        sys.executable,
        "run_qarb_080_single_runtime_dynamic_mriya_supervisor.py",
        "--worker",
        "--bindings",
        str(path),
        "--generation",
        str(generation),
        "--seconds",
        str(drain_seconds),
        "--admit-seconds",
        str(admit_seconds)
    ]

def normalize_windows(
    refresh_seconds,
    drain_seconds
):
    refresh=max(
        MIN_REFRESH_SECONDS,
        float(refresh_seconds)
    )

    drain=max(
        float(drain_seconds),
        refresh+DRAIN_TAIL_SECONDS
    )

    return refresh,drain

def run(
    seconds=None,
    refresh_seconds=60.0,
    drain_seconds=155.0
):
    root=Path.cwd()

    refresh_seconds,drain_seconds=normalize_windows(
        refresh_seconds,
        drain_seconds
    )

    q61d.CONNECTION_STAGGER_SECONDS=WS_CONNECTION_STAGGER_SECONDS
    q61d.install()

    discovery=subprocess.Popen(
        [
            sys.executable,
            "run_qarb_043b_paced_mriya_token_discovery.py"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    children=[]
    started=time.monotonic()
    generation=0
    transport_failures=0

    print(
        "[QARB-080] SINGLE-RUNTIME DYNAMIC MRIYA SUPERVISOR",
        flush=True
    )

    print(
        "[DISCOVERY] silent background Mriya intake",
        flush=True
    )

    print(
        "[LEARNING] 047B age lineage + 073 durable profitability outcomes",
        flush=True
    )

    print(
        "[HYDRATION_POLICY] serialized=True refresh=%.1fs drain=%.1fs horizon=%.1fs"%(
            refresh_seconds,
            drain_seconds,
            MAX_HORIZON_SECONDS
        ),
        flush=True
    )

    print(
        "[WS_CAP] max_accounts_per_connection=%d stagger=%.2fs"%(
            q61d.MAX_SUBSCRIPTIONS_PER_CONNECTION,
            q61d.CONNECTION_STAGGER_SECONDS
        ),
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",
        flush=True
    )

    try:
        time.sleep(6.0)

        while (
            seconds is None
            or time.monotonic()-started<float(seconds)
        ):
            _,fresh=q45.classify()

            rows=select_rows(
                root,
                fresh
            )

            introduced,returned=announce(
                root,
                rows
            )

            if rows:
                generation+=1

                path=q47.write_generation(
                    rows,
                    generation
                )

                children.append(
                    subprocess.Popen(
                        worker_cmd(
                            path,
                            generation,
                            drain_seconds,
                            refresh_seconds
                        )
                    )
                )

                print(
                    "[ROTATION] generation=%d usable=%d new=%d returns=%d"%(
                        generation,
                        len(rows),
                        len(introduced),
                        len(returned)
                    ),
                    flush=True
                )

            else:
                print(
                    "[ROTATION_HOLD] no exact-bound usable tokens",
                    flush=True
                )

            alive=[]
            for ch in children:
                rc=ch.poll()
                if rc is None:
                    alive.append(ch)
                elif rc!=0:
                    transport_failures+=1
            children=alive

            _save(
                root/STATE,
                {
                    "revision":"QARB_080",
                    "generation":generation,
                    "usable_tokens":[
                        x["token"]
                        for x in rows
                    ],
                    "child_generations_running":
                        sum(
                            x.poll() is None
                            for x in children
                        ),
                    "discovery_alive":
                        discovery.poll() is None,
                    "refresh_seconds":
                        refresh_seconds,
                    "drain_seconds":
                        drain_seconds,
                    "hydration_serialized":
                        True,
                    "transport_failures":
                        transport_failures,
                    "ws_cap":
                        q61d.MAX_SUBSCRIPTIONS_PER_CONNECTION,
                    "ws_stagger_seconds":
                        q61d.CONNECTION_STAGGER_SECONDS,
                    "execution_authority":
                        False,
                    "paper_only":
                        True,
                    "real_money_moved":
                        False
                }
            )

            remain=(
                None
                if seconds is None
                else float(seconds)-(
                    time.monotonic()-started
                )
            )

            if (
                remain is not None
                and remain<=0
            ):
                break

            time.sleep(
                refresh_seconds
                if remain is None
                else min(
                    refresh_seconds,
                    remain
                )
            )

    finally:
        try:
            discovery.terminate()
        except Exception:
            pass

        deadline=(
            time.time()
            +drain_seconds
            +5.0
        )

        for ch in children:
            try:
                rc=ch.wait(
                    timeout=max(
                        1.0,
                        deadline-time.time()
                    )
                )
                if rc not in (None,0):
                    transport_failures+=1
            except Exception:
                transport_failures+=1
                try:
                    ch.terminate()
                except Exception:
                    pass

    transport_status="PASS" if transport_failures==0 else "HOLD"

    print(
        "[WS_TRANSPORT_FINAL] status=%s failed_generations=%d"%(
            transport_status,
            transport_failures
        ),
        flush=True
    )

    print(
        "[RUNTIME_DONE] generations=%d execution_authority=FALSE"%generation,
        flush=True
    )

    return 0 if transport_failures==0 else 2

def main(argv=None):
    import argparse

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=None
    )

    ap.add_argument(
        "--refresh-seconds",
        type=float,
        default=60.0
    )

    ap.add_argument(
        "--drain-seconds",
        type=float,
        default=155.0
    )

    ap.add_argument(
        "--worker",
        action="store_true"
    )

    ap.add_argument(
        "--bindings"
    )

    ap.add_argument(
        "--generation",
        type=int,
        default=0
    )

    ap.add_argument(
        "--admit-seconds",
        type=float,
        default=60.0
    )

    a=ap.parse_args(argv)

    if a.worker:
        return asyncio.run(
            generation_worker(
                a.bindings,
                a.seconds,
                a.admit_seconds,
                a.generation
            )
        )

    return run(
        a.seconds,
        a.refresh_seconds,
        a.drain_seconds
    )

if __name__=="__main__":
    raise SystemExit(main())
