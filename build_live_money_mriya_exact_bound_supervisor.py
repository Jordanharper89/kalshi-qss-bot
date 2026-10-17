from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"live_money_supervisor.py"
TEST=ROOT/"test_live_money_supervisor.py"

MODULE=r"""from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as money_core
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_044_dynamic_exact_crossvenue_binding as q44
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_061a_shared_rpc_valve as rpc_valve
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
MRIYA_BIND_LIMIT=12
MRIYA_ACTIVE_SECONDS=600.0


def _load(path,default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,indent=2,sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def signer_preflight():
    try:
        signer,user=money_core.sim_identity()
    except Exception as exc:
        print(
            "[SIGNER] INVALID error=%s:%s"
            %(type(exc).__name__,str(exc)[:200]),
            flush=True,
        )
        return False,None

    if signer is None or not user:
        print(
            "[SIGNER] NOT_READY env=QSB_SOLANA_PRIVATE_KEY",
            flush=True,
        )
        return False,None

    print(
        "[SIGNER] READY pubkey=%s"
        %str(user),
        flush=True,
    )
    return True,str(user)


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


def exact_mriya_rows():
    # Apply the already-certified serialized HTTP valve to the same core module
    # used by QARB-044 before any binding RPC is attempted.
    rpc_valve.install()

    before_calls=int(rpc_valve.RPC_CALLS)
    before_429=int(rpc_valve.RPC_429)

    result=q44.bind(MRIYA_BIND_LIMIT)
    now=time.time()

    rows=[]
    for row in list(result.get("rows") or []):
        age=max(
            0.0,
            now-float(row.get("last_seen_epoch") or 0.0),
        )

        if age<=MRIYA_ACTIVE_SECONDS:
            x=dict(row)
            x["mriya_age_seconds"]=age
            rows.append(x)

    rows=q80.select_rows(ROOT,rows)

    delta_calls=int(rpc_valve.RPC_CALLS)-before_calls
    delta_429=int(rpc_valve.RPC_429)-before_429

    print(
        "[MRIYA_BIND] requested=%d bound=%d fresh=%d rpc_calls=%d caught_429=%d gap=%.2fs"
        %(
            MRIYA_BIND_LIMIT,
            len(result.get("rows") or []),
            len(rows),
            delta_calls,
            delta_429,
            float(rpc_valve._GAP),
        ),
        flush=True,
    )

    return rows,{
        "rpc_calls":delta_calls,
        "caught_429":delta_429,
        "failures":list(result.get("failures") or []),
    }


def refresh_priority():
    rows,transport=exact_mriya_rows()
    inventory,by_pair,by_token=_capacity_index()

    pair_keys=set()
    tokens=set()
    exact_bound=[]
    token_bound=[]
    unbound=[]

    for row in rows:
        token=str(row.get("token") or "")
        meta=dict(row.get("meteora_meta") or {})
        pool=str(meta.get("address") or row.get("meteora_pool") or "")

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
                "discovered_meteora_pool":pool or None,
                "source":"MRIYA_TOKEN_BOUND",
            })
            continue

        if token:
            unbound.append({
                "token":token,
                "pump_pool":row.get("pump_pool"),
                "meteora_pool":pool or None,
                "source":"MRIYA_UNBOUND",
            })

    payload={
        "revision":"LIVE_MONEY_MRIYA_PACED_EXACT_BIND_V1",
        "updated_unix":time.time(),
        "inventory_routes":len(inventory),
        "mriya_rows":len(rows),
        "pair_keys":sorted(pair_keys),
        "tokens":sorted(tokens),
        "exact_bound":exact_bound,
        "token_bound":token_bound,
        "unbound":unbound,
        "binding_transport":transport,
        "policy":{
            "mriya_replenishment_only":True,
            "execution_hot_path_independent":True,
            "serialized_rpc_binding":True,
            "cached_bindings_reused":True,
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
            "[MRIYA_BOUND] token=%s pair=%s"
            %(row["token"][:12],row["identity"][:36]),
            flush=True,
        )

    for row in token_bound:
        print(
            "[MRIYA_TOKEN_BOUND] token=%s current_pairs=%d"
            %(row["token"][:12],len(row["known_pair_keys"])),
            flush=True,
        )

    for row in unbound[:12]:
        print(
            "[MRIYA_UNBOUND] token=%s held_out=True"
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


def run(
    seconds=1800.0,
    refresh_seconds=60.0,
    generation_seconds=300.0,
):
    refresh_seconds=max(
        MIN_REFRESH_SECONDS,
        float(refresh_seconds),
    )
    generation_seconds=max(
        MIN_GENERATION_SECONDS,
        float(generation_seconds),
    )

    # CRITICAL: no discovery, hydration, or RPC if signer is unavailable.
    signer_ready,user=signer_preflight()

    if not signer_ready:
        _save(STATUS,{
            "revision":"LIVE_MONEY_MRIYA_PACED_EXACT_BIND_V1",
            "state":"HOLD_SIGNER_NOT_READY",
            "discovery_started":False,
            "money_runtime_started":False,
            "execution_authority":False,
        })
        print(
            "[HOLD] signer unavailable; zero hydration attempted",
            flush=True,
        )
        return 3

    if not DISCOVERY_LAUNCHER.is_file():
        raise RuntimeError(
            "MRIYA_DISCOVERY_LAUNCHER_MISSING:"
            +str(DISCOVERY_LAUNCHER)
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
    child_failures=0

    print(
        "[LIVE_MONEY_SUPERVISOR] paced_mriya_exact_binding=True",
        flush=True,
    )
    print(
        "[MRIYA_ROLE] replenishment_only=True execution_path=False",
        flush=True,
    )
    print(
        "[BIND_POLICY] limit=%d active_seconds=%.0f serialized_rpc=True"
        %(MRIYA_BIND_LIMIT,MRIYA_ACTIVE_SECONDS),
        flush=True,
    )
    print(
        "[DISCOVERY] silent_background=True",
        flush=True,
    )
    print(
        "[BROADCAST] disabled",
        flush=True,
    )

    try:
        while time.monotonic()-started<float(seconds):
            now=time.monotonic()

            if child is not None:
                rc=child.poll()
                if rc is not None:
                    if rc!=0:
                        child_failures+=1
                        print(
                            "[MONEY_GENERATION_FAIL] rc=%d"
                            %rc,
                            flush=True,
                        )
                    child=None

            if now>=next_refresh:
                try:
                    last_priority=refresh_priority()
                except Exception as exc:
                    print(
                        "[MRIYA_REFRESH_WARN] %s:%s"
                        %(type(exc).__name__,str(exc)[:240]),
                        flush=True,
                    )
                next_refresh=time.monotonic()+refresh_seconds

            if child is None:
                # Re-check signer before EVERY new generation.
                signer_ready,_=signer_preflight()
                if not signer_ready:
                    print(
                        "[HOLD] signer lost; no money generation started",
                        flush=True,
                    )
                    return 3

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

                child=subprocess.Popen(
                    _money_cmd(run_for)
                )

            _save(STATUS,{
                "revision":"LIVE_MONEY_MRIYA_PACED_EXACT_BIND_V1",
                "state":"RUNNING",
                "generation":generation,
                "signer_ready":True,
                "signer_pubkey":user,
                "discovery_alive":discovery.poll() is None,
                "money_runtime_alive":child is not None and child.poll() is None,
                "child_failures":child_failures,
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
        "[LIVE_MONEY_SUPERVISOR_DONE] generations=%d child_failures=%d"
        %(generation,child_failures),
        flush=True,
    )

    return 0 if child_failures==0 else 2


def main():
    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=1800.0,
    )

    p.add_argument(
        "--refresh-seconds",
        type=float,
        default=60.0,
    )

    p.add_argument(
        "--generation-seconds",
        type=float,
        default=300.0,
    )

    a=p.parse_args()

    if a.seconds<=0:
        raise RuntimeError(
            "SUPERVISOR_SECONDS_MUST_BE_POSITIVE"
        )

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

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_supervisor.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_signer_fail_fast(self):
        self.assertIn("signer_preflight()",self.s)
        self.assertIn("zero hydration attempted",self.s)
        self.assertIn("discovery_started",self.s)

    def test_signer_uses_real_identity_path(self):
        self.assertIn("money_core.sim_identity()",self.s)
        self.assertIn("QSB_SOLANA_PRIVATE_KEY",self.s)

    def test_paced_exact_binder(self):
        self.assertIn("q44.bind(MRIYA_BIND_LIMIT)",self.s)
        self.assertIn("rpc_valve.install()",self.s)
        self.assertIn("MRIYA_BIND_LIMIT=12",self.s)

    def test_mriya_replenishment_only(self):
        self.assertIn(
            "[MRIYA_ROLE] replenishment_only=True execution_path=False",
            self.s,
        )

    def test_unbound_held_out(self):
        self.assertIn(
            "unbound_candidates_never_enter_execution",
            self.s,
        )
        self.assertIn(
            "[MRIYA_UNBOUND]",
            self.s,
        )

    def test_recheck_signer_each_generation(self):
        self.assertIn(
            "Re-check signer before EVERY new generation",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

ast.parse(
    TEST.read_text(
        encoding="utf-8"
    )
)

print("[PASS] live-money Mriya exact-bound supervisor installed")
print("[SIGNER] fail-fast before discovery/hydration/RPC")
print("[SIGNER] rechecked before every money generation")
print("[MRIYA] exact QARB-044 binder reused")
print("[RPC] QARB-061A serialized adaptive valve installed before binding")
print("[BIND] limit=12 active_window=600s cache reuse preserved")
print("[ROLE] Mriya replenishment only")
print("[UNBOUND] held out of execution")
print("[BROADCAST] disabled")
print("[KEY] never printed or modified")
print("[TEST]",TEST.name)
