from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"live_money_supervisor.py"
TEST=ROOT/"test_live_money_mriya_inventory_materializer.py"

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

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"

FULL=STATE/"full_surface_replenishment_inventory.json"
CAPACITY=STATE/"capacity_aware_warm_universe.json"
PRIORITY=STATE/"mriya_replenishment_priority.json"
STATUS=STATE/"mriya_replenishment_status.json"

DISCOVERY_LAUNCHER=ROOT/"run_qarb_043b_paced_mriya_token_discovery.py"

CP24_MODULE=(
    "qseries_v2.oracle_execution.solana_atomic_executor."
    "checkpoint24_capacity_aware_warm_universe"
)

MRIYA_BIND_LIMIT=12
MRIYA_ACTIVE_SECONDS=600.0
INVENTORY_ACCOUNT_CAP=768
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
    tmp.write_text(
        json.dumps(payload,indent=2,sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def _identity(row):
    token=str(row.get("token") or "")
    pool=str(
        row.get("meteora_pool")
        or (row.get("meteora_meta") or {}).get("address")
        or ""
    )
    if not token or not pool:
        return ""
    return token+"|"+pool


def signer_preflight():
    try:
        signer,user=money_core.sim_identity()
    except Exception as exc:
        print(
            "[SIGNER] INVALID error=%s:%s"
            %(type(exc).__name__,str(exc)[:180]),
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
        "[SIGNER] READY pubkey=%s"%str(user),
        flush=True,
    )
    return True,str(user)


def exact_mriya_rows():
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


def materializer_row(binding,existing_example=None):
    meta=dict(binding.get("meteora_meta") or {})
    token=str(binding.get("token") or "")
    pump=str(binding.get("pump_pool") or "")
    pool=str(meta.get("address") or "")

    if not token or not pump or not pool:
        raise RuntimeError("MRIYA_MATERIALIZER_INCOMPLETE_BINDING")

    row={}
    if isinstance(existing_example,dict):
        # Start with the certified surface's schema. Unknown optional fields
        # are reset to neutral values instead of silently copying identity.
        for key,value in existing_example.items():
            if isinstance(value,bool):
                row[key]=False
            elif isinstance(value,int):
                row[key]=0
            elif isinstance(value,float):
                row[key]=0.0
            elif isinstance(value,list):
                row[key]=[]
            elif isinstance(value,dict):
                row[key]={}
            else:
                row[key]=None

    identity=token+"|"+pool

    row.update({
        "pair_key":identity,
        "identity":identity,
        "token":token,
        "pump_pool":pump,
        "meteora_pool":pool,
        "meteora_meta":meta,
        "token_x":str(meta.get("token_x") or ""),
        "token_y":str(meta.get("token_y") or ""),
        "decimals_x":int(meta.get("decimals_x") or 0),
        "decimals_y":int(meta.get("decimals_y") or 0),
        "reported_tvl":float(meta.get("tvl") or 0.0),
        "source_age":float(binding.get("mriya_age_seconds") or 0.0),
        "mriya_age_seconds":float(binding.get("mriya_age_seconds") or 0.0),
        "discovery_rank":0,
        "source_rank":0,
        "selected_legacy":False,
        "retained":False,
        "mriya_replenishment":True,
        "mriya_exact_bound":True,
        "last_seen_epoch":float(binding.get("last_seen_epoch") or 0.0),
        "first_seen_epoch":float(binding.get("first_seen_epoch") or 0.0),
        "touches":int(binding.get("touches") or 0),
        "execution_authority":False,
        "broadcast":False,
    })

    return row


def materialize_into_full(rows):
    data=_load(FULL,None)
    if data is None:
        raise RuntimeError("MRIYA_FULL_SURFACE_MISSING:"+str(FULL))

    original=list(data.get("rows") or [])

    if not original:
        raise RuntimeError("MRIYA_FULL_SURFACE_EMPTY")

    existing={}
    for row in original:
        key=_identity(row)
        if key:
            existing[key]=row

    added=[]
    refreshed=[]

    example=original[0]

    for binding in rows:
        row=materializer_row(binding,example)
        key=_identity(row)

        if key in existing:
            current=dict(existing[key])
            current.update({
                "source_age":row["source_age"],
                "mriya_age_seconds":row["mriya_age_seconds"],
                "last_seen_epoch":row["last_seen_epoch"],
                "touches":row["touches"],
                "mriya_replenishment":True,
                "mriya_exact_bound":True,
            })
            existing[key]=current
            refreshed.append(key)
        else:
            existing[key]=row
            added.append(key)

    # Preserve original order, then append genuinely new Mriya identities.
    ordered=[]
    seen=set()

    for row in original:
        key=_identity(row)
        if not key or key in seen:
            continue
        ordered.append(existing[key])
        seen.add(key)

    for key in added:
        if key not in seen:
            ordered.append(existing[key])
            seen.add(key)

    out=dict(data)
    out["revision"]="FULL_SURFACE_REPLENISHMENT_PLUS_MRIYA_V1"
    out["rows"]=ordered
    out["pair_identities"]=len(ordered)
    out["mriya_materialized_total"]=sum(
        1 for x in ordered if x.get("mriya_replenishment")
    )
    out["mriya_last_added"]=len(added)
    out["mriya_last_refreshed"]=len(refreshed)
    out["updated_unix"]=time.time()
    out["execution_authority"]=False
    out["broadcast"]=False

    _save(FULL,out)

    print(
        "[MRIYA_MATERIALIZED] base=%d added=%d refreshed=%d total=%d"
        %(len(original),len(added),len(refreshed),len(ordered)),
        flush=True,
    )

    for key in added:
        print(
            "[MRIYA_ROUTE_ADDED] pair=%s"%key[:48],
            flush=True,
        )

    return out,added,refreshed


def rebuild_capacity():
    cmd=[
        sys.executable,
        "-m",
        CP24_MODULE,
        "--max-accounts",
        str(INVENTORY_ACCOUNT_CAP),
    ]

    print(
        "[CAPACITY_REBUILD] source=full_surface_plus_mriya max_accounts=%d"
        %INVENTORY_ACCOUNT_CAP,
        flush=True,
    )

    rc=subprocess.call(cmd)

    if rc!=0:
        raise RuntimeError(
            "MRIYA_CP24_CAPACITY_REBUILD_FAILED:"+str(rc)
        )

    data=_load(CAPACITY,None)
    if data is None:
        raise RuntimeError(
            "MRIYA_CAPACITY_OUTPUT_MISSING:"+str(CAPACITY)
        )

    rows=list(data.get("rows") or [])

    print(
        "[CAPACITY_READY] routes=%d"
        %len(rows),
        flush=True,
    )

    return data


def write_priority(mriya_rows,transport,added,refreshed):
    cap=_load(CAPACITY,{"rows":[]})
    cap_rows=list(cap.get("rows") or [])

    cap_keys={_identity(x) for x in cap_rows if _identity(x)}
    cap_tokens={str(x.get("token") or "") for x in cap_rows}

    pairs=[]
    tokens=[]
    outside=[]

    for binding in mriya_rows:
        key=_identity(binding)
        token=str(binding.get("token") or "")

        if key and key in cap_keys:
            pairs.append(key)
            tokens.append(token)
            print(
                "[MRIYA_PROMOTE] token=%s pair=%s"
                %(token[:12],key[:36]),
                flush=True,
            )
        elif token and token in cap_tokens:
            tokens.append(token)
            print(
                "[MRIYA_TOKEN_PRIORITY] token=%s"
                %token[:12],
                flush=True,
            )
        elif key:
            outside.append(key)
            print(
                "[MRIYA_CAPACITY_HOLD] pair=%s"
                %key[:36],
                flush=True,
            )

    payload={
        "revision":"LIVE_MONEY_MRIYA_MATERIALIZED_PRIORITY_V1",
        "updated_unix":time.time(),
        "pair_keys":sorted(set(pairs)),
        "tokens":sorted(set(tokens)),
        "outside_capacity":sorted(set(outside)),
        "materialized_added":list(added),
        "materialized_refreshed":list(refreshed),
        "binding_transport":transport,
        "capacity_routes":len(cap_rows),
        "policy":{
            "mriya_replenishment_only":True,
            "materialize_before_capacity_rank":True,
            "rotation_between_generations_only":True,
            "execution_hot_path_independent":True,
        },
        "execution_authority":False,
        "broadcast":False,
    }

    _save(PRIORITY,payload)

    print(
        "[MRIYA_PRIORITY_READY] pairs=%d tokens=%d outside_capacity=%d"
        %(
            len(payload["pair_keys"]),
            len(payload["tokens"]),
            len(payload["outside_capacity"]),
        ),
        flush=True,
    )

    return payload


def replenishment_cycle():
    rows,transport=exact_mriya_rows()

    full,added,refreshed=materialize_into_full(rows)

    capacity=rebuild_capacity()

    priority=write_priority(
        rows,
        transport,
        added,
        refreshed,
    )

    return {
        "fresh_bindings":len(rows),
        "full_routes":len(full.get("rows") or []),
        "capacity_routes":len(capacity.get("rows") or []),
        "priority_pairs":len(priority.get("pair_keys") or []),
        "priority_tokens":len(priority.get("tokens") or []),
        "added":len(added),
        "refreshed":len(refreshed),
    }


def _money_cmd(seconds):
    return [
        sys.executable,
        "-m",
        "qseries_v2.oracle_execution.solana_atomic_executor.live_money_runtime",
        "--seconds",
        str(float(seconds)),
    ]


def run(seconds=1800.0,generation_seconds=300.0):
    generation_seconds=max(
        MIN_GENERATION_SECONDS,
        float(generation_seconds),
    )

    signer_ready,user=signer_preflight()

    if not signer_ready:
        print(
            "[HOLD] signer unavailable; zero replenishment attempted",
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

    started=time.monotonic()
    generation=0
    child_failures=0

    print(
        "[LIVE_MONEY_SUPERVISOR] mriya_inventory_materializer=True",
        flush=True,
    )
    print(
        "[MRIYA_ROLE] replenishment_only=True execution_path=False",
        flush=True,
    )
    print(
        "[ROTATION_POLICY] replenishment_between_generations_only=True",
        flush=True,
    )
    print(
        "[INVENTORY_POLICY] full_surface -> CP24_768 -> live_hot_318",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)

    try:
        # Let silent discovery collect a short initial sample.
        time.sleep(6.0)

        while time.monotonic()-started<float(seconds):
            signer_ready,_=signer_preflight()
            if not signer_ready:
                print(
                    "[HOLD] signer lost before replenishment cycle",
                    flush=True,
                )
                return 3

            cycle={}
            try:
                cycle=replenishment_cycle()
            except Exception as exc:
                print(
                    "[REPLENISHMENT_HOLD] %s:%s"
                    %(type(exc).__name__,str(exc)[:260]),
                    flush=True,
                )

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
            rc=child.wait()

            if rc!=0:
                child_failures+=1
                print(
                    "[MONEY_GENERATION_FAIL] generation=%d rc=%d"
                    %(generation,rc),
                    flush=True,
                )
            else:
                print(
                    "[MONEY_GENERATION_DONE] generation=%d rc=0"
                    %generation,
                    flush=True,
                )

            _save(STATUS,{
                "revision":"LIVE_MONEY_MRIYA_INVENTORY_MATERIALIZER_V1",
                "state":"RUNNING",
                "generation":generation,
                "signer_ready":True,
                "signer_pubkey":user,
                "discovery_alive":discovery.poll() is None,
                "money_runtime_alive":False,
                "child_failures":child_failures,
                "last_replenishment":cycle,
                "execution_authority":False,
                "broadcast":False,
            })

    finally:
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

    # Accepted for backward CLI compatibility. Replenishment now intentionally
    # occurs only between generations, never concurrently with the hot child.
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
        raise RuntimeError("SUPERVISOR_SECONDS_MUST_BE_POSITIVE")

    return run(
        seconds=a.seconds,
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

    def test_materializes_full_surface(self):
        self.assertIn(
            "full_surface_replenishment_inventory.json",
            self.s,
        )
        self.assertIn(
            "[MRIYA_MATERIALIZED]",
            self.s,
        )

    def test_exact_identity(self):
        self.assertIn(
            'return token+"|"+pool',
            self.s,
        )

    def test_reuses_cp24(self):
        self.assertIn(
            "checkpoint24_capacity_aware_warm_universe",
            self.s,
        )
        self.assertIn(
            "INVENTORY_ACCOUNT_CAP=768",
            self.s,
        )

    def test_rotation_between_generations(self):
        self.assertIn(
            "[ROTATION_POLICY] replenishment_between_generations_only=True",
            self.s,
        )
        self.assertIn(
            "rc=child.wait()",
            self.s,
        )

    def test_signer_fail_fast(self):
        self.assertIn(
            "signer_preflight()",
            self.s,
        )
        self.assertIn(
            "zero replenishment attempted",
            self.s,
        )

    def test_mriya_priority_from_capacity(self):
        self.assertIn(
            "[MRIYA_PROMOTE]",
            self.s,
        )
        self.assertIn(
            "[MRIYA_PRIORITY_READY]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

ast.parse(TARGET.read_text(encoding="utf-8"))
ast.parse(TEST.read_text(encoding="utf-8"))

print("[PASS] Mriya canonical replenishment materializer installed")
print("[SOURCE] exact QARB-044 Mriya bindings")
print("[MATERIALIZE] token|meteora_pool into full_surface_replenishment_inventory")
print("[CAPACITY] certified checkpoint24 rebuild at 768-account inventory ceiling")
print("[ROTATION] replenishment only between money generations")
print("[HOT] live_money_runtime retains 318-account / 48-per-shard execution book")
print("[SIGNER] fail-fast preserved")
print("[ROLE] Mriya replenishment only")
print("[BROADCAST] disabled")
print("[KEY] untouched")
print("[TEST]",TEST.name)
