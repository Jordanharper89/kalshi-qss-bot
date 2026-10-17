from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path.cwd()
STATE_DIR=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"
ACTIVE_PATH=STATE_DIR/"active_after_fee_pairs.json"
PRIORITY_PATH=STATE_DIR/"mriya_replenishment_priority.json"
CAPACITY_PATH=STATE_DIR/"capacity_aware_warm_universe.json"

ACTIVE_TTL_SECONDS=1800.0
MAX_ACTIVE_PAIRS=12

WINNER_RE=re.compile(
    r"\[CHECKPOINT19_WINNER\]\s+"
    r"pair=(\S+).*?"
    r"dir=(\S+).*?"
    r"size=([0-9.]+).*?"
    r"after_fee=([+-]?\d+)"
)

SIM_PASS_RE=re.compile(
    r"\[CHECKPOINT19_SIGNED_SIM_PASS\]\s+"
    r"pair=(\S+)"
)


def _load(path,default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(row,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)


def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj,list):
        for value in obj:
            yield from _walk(value)


def _inventory_pairs():
    src=_load(CAPACITY_PATH,{})
    rows={}
    for obj in _walk(src):
        token=str(obj.get("token") or obj.get("mint") or "").strip()
        pool=str(
            obj.get("meteora_pool")
            or obj.get("meteora")
            or obj.get("pool")
            or ""
        ).strip()
        pair_key=str(obj.get("pair_key") or "").strip()

        if "|" in pair_key:
            left,right=pair_key.split("|",1)
            token=token or left
            pool=pool or right

        if not token or not pool:
            continue

        key=token+"|"+pool
        rows[key]={
            "pair_key":key,
            "token":token,
            "meteora_pool":pool,
        }
    return rows


def _resolve_prefix(prefix,inventory):
    prefix=str(prefix).strip()
    hits=[
        row for key,row in inventory.items()
        if key.startswith(prefix) or row["token"].startswith(prefix)
    ]
    exact={row["pair_key"]:row for row in hits}
    if len(exact)==1:
        return next(iter(exact.values()))
    return None


def _prune_active(active,now=None):
    now=time.time() if now is None else float(now)
    rows=[]
    for row in list(active.get("pairs") or []):
        last=float(row.get("last_after_fee_positive_unix") or 0.0)
        if last<=0:
            continue
        if now-last>ACTIVE_TTL_SECONDS:
            continue
        rows.append(dict(row))

    rows.sort(
        key=lambda x:(
            int(x.get("best_after_fee_lamports") or 0),
            float(x.get("last_after_fee_positive_unix") or 0.0),
        ),
        reverse=True,
    )
    rows=rows[:MAX_ACTIVE_PAIRS]
    return {
        "revision":"ACTIVE_AFTER_FEE_PAIRS_V1",
        "ttl_seconds":ACTIVE_TTL_SECONDS,
        "pairs":rows,
        "updated_unix":now,
        "broadcast":False,
    }


def _record_positive(active,resolved,direction,size_sol,after_fee,now=None):
    now=time.time() if now is None else float(now)
    by_key={
        str(row.get("pair_key")):dict(row)
        for row in list(active.get("pairs") or [])
        if row.get("pair_key")
    }

    key=resolved["pair_key"]
    row=by_key.get(
        key,
        {
            "pair_key":key,
            "token":resolved["token"],
            "meteora_pool":resolved["meteora_pool"],
            "positive_observations":0,
            "signed_sim_passes":0,
            "best_after_fee_lamports":0,
        },
    )

    row["positive_observations"]=int(row.get("positive_observations") or 0)+1
    row["last_after_fee_positive_unix"]=now
    row["last_direction"]=str(direction)
    row["last_size_sol"]=float(size_sol)
    row["last_after_fee_lamports"]=int(after_fee)
    row["best_after_fee_lamports"]=max(
        int(row.get("best_after_fee_lamports") or 0),
        int(after_fee),
    )
    row["source"]="LIVE_AFTER_FEE"
    row["sticky"]=True
    by_key[key]=row
    active["pairs"]=list(by_key.values())
    return _prune_active(active,now)


def _mark_sim_pass(active,prefix,inventory,now=None):
    now=time.time() if now is None else float(now)
    resolved=_resolve_prefix(prefix,inventory)
    if resolved is None:
        return active,None

    key=resolved["pair_key"]
    for row in list(active.get("pairs") or []):
        if row.get("pair_key")!=key:
            continue
        row["signed_sim_passes"]=int(row.get("signed_sim_passes") or 0)+1
        row["last_signed_sim_pass_unix"]=now
        row["source"]="SIGNED_SIM_PASS"
        return _prune_active(active,now),row
    return active,None


def _merge_active_into_priority(active):
    priority=_load(PRIORITY_PATH,{})
    if not isinstance(priority,dict):
        priority={}

    current_pairs=list(priority.get("pairs") or [])
    pair_map={}

    for row in current_pairs:
        if isinstance(row,str):
            pair_map[row]={"pair_key":row,"source":"MRIYA"}
        elif isinstance(row,dict):
            key=str(row.get("pair_key") or "")
            if key:
                pair_map[key]=dict(row)

    for row in list(active.get("pairs") or []):
        key=str(row["pair_key"])
        pair_map[key]={
            "pair_key":key,
            "token":row["token"],
            "meteora_pool":row["meteora_pool"],
            "source":"ACTIVE_AFTER_FEE",
            "sticky":True,
            "best_after_fee_lamports":int(row.get("best_after_fee_lamports") or 0),
            "last_after_fee_positive_unix":float(
                row.get("last_after_fee_positive_unix") or 0.0
            ),
        }

    rows=list(pair_map.values())
    rows.sort(
        key=lambda x:(
            x.get("source")=="ACTIVE_AFTER_FEE",
            int(x.get("best_after_fee_lamports") or 0),
        ),
        reverse=True,
    )

    priority["pairs"]=rows
    tokens=[]
    seen=set()

    for row in rows:
        token=str(row.get("token") or "")
        if not token and "|" in str(row.get("pair_key") or ""):
            token=str(row["pair_key"]).split("|",1)[0]
        if token and token not in seen:
            seen.add(token)
            tokens.append(token)

    priority["tokens"]=tokens
    priority["active_after_fee_pairs"]=sum(
        row.get("source")=="ACTIVE_AFTER_FEE" for row in rows
    )
    priority["updated_unix"]=time.time()
    priority["broadcast"]=False
    _save(PRIORITY_PATH,priority)

    print(
        "[ACTIVE_PRIORITY_READY] active=%d total_priority=%d"
        %(priority["active_after_fee_pairs"],len(rows)),
        flush=True,
    )
    return priority


def _supervisor_command(seconds,refresh_seconds):
    return [
        sys.executable,
        "-m",
        "qseries_v2.oracle_execution.solana_atomic_executor.live_money_supervisor",
        "--seconds",str(float(seconds)),
        "--refresh-seconds",str(float(refresh_seconds)),
        "--generation-seconds",str(float(seconds)),
    ]


def _run_generation(generation,seconds,refresh_seconds,active):
    print(
        "[MONEY_DRIVER_GENERATION_START] generation=%d seconds=%.0f"
        %(generation,seconds),
        flush=True,
    )

    proc=subprocess.Popen(
        _supervisor_command(seconds,refresh_seconds),
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )

    unresolved=[]
    positives=0
    sim_passes=0
    assert proc.stdout is not None

    for raw in proc.stdout:
        line=raw.rstrip("\r\n")
        print(line,flush=True)

        if "[MRIYA_PRIORITY_READY]" in line or "[MONEY_GENERATION_START]" in line:
            active=_prune_active(active)
            _merge_active_into_priority(active)

        m=WINNER_RE.search(line)
        if m:
            prefix,direction,size,after_fee=m.groups()
            after_fee=int(after_fee)
            if after_fee>0:
                inventory=_inventory_pairs()
                resolved=_resolve_prefix(prefix,inventory)
                if resolved is None:
                    unresolved.append(prefix)
                    print(
                        "[ACTIVE_PROFIT_HOLD] prefix=%s reason=EXACT_PAIR_NOT_UNIQUE"
                        %prefix,
                        flush=True,
                    )
                else:
                    active=_record_positive(
                        active,resolved,direction,float(size),after_fee
                    )
                    _save(ACTIVE_PATH,active)
                    positives+=1
                    print(
                        "[ACTIVE_PROFIT_PROMOTE] pair=%s dir=%s size=%s "
                        "after_fee=%+d sticky=True"
                        %(resolved["pair_key"],direction,size,after_fee),
                        flush=True,
                    )

        s=SIM_PASS_RE.search(line)
        if s:
            active,row=_mark_sim_pass(active,s.group(1),_inventory_pairs())
            if row is not None:
                _save(ACTIVE_PATH,active)
                sim_passes+=1
                print(
                    "[ACTIVE_SIM_CERTIFIED] pair=%s passes=%d"
                    %(row["pair_key"],row["signed_sim_passes"]),
                    flush=True,
                )

    rc=proc.wait()
    active=_prune_active(active)
    _save(ACTIVE_PATH,active)
    _merge_active_into_priority(active)

    print(
        "[MONEY_DRIVER_GENERATION_DONE] generation=%d rc=%d "
        "positives=%d sim_passes=%d active_pairs=%d unresolved=%d"
        %(generation,rc,positives,sim_passes,len(active.get("pairs") or []),len(unresolved)),
        flush=True,
    )
    return rc,active


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=1800.0)
    ap.add_argument("--generation-seconds",type=float,default=300.0)
    ap.add_argument("--refresh-seconds",type=float,default=60.0)
    args=ap.parse_args(argv)

    if args.seconds<=0:
        raise RuntimeError("MONEY_DRIVER_SECONDS_MUST_BE_POSITIVE")
    if args.generation_seconds<90:
        raise RuntimeError("MONEY_DRIVER_GENERATION_TOO_SHORT")

    STATE_DIR.mkdir(parents=True,exist_ok=True)
    active=_prune_active(_load(ACTIVE_PATH,{"pairs":[]}))
    _save(ACTIVE_PATH,active)
    _merge_active_into_priority(active)

    print(
        "[LIVE_MONEY_DRIVER] canonical_supervisor=True "
        "active_after_fee_retention=True mriya_replenishment_preserved=True",
        flush=True,
    )
    print(
        "[ACTIVE_POLICY] exact_pair_only=True ttl_seconds=%.0f max_pairs=%d"
        %(ACTIVE_TTL_SECONDS,MAX_ACTIVE_PAIRS),
        flush=True,
    )
    print("[LIVE_SEND] DISABLED until signed-sim certification",flush=True)
    print("[BROADCAST] disabled",flush=True)

    deadline=time.monotonic()+float(args.seconds)
    generation=0
    child_failures=0

    while time.monotonic()<deadline:
        remain=deadline-time.monotonic()
        if remain<90:
            break

        generation+=1
        seconds=min(float(args.generation_seconds),remain)
        rc,active=_run_generation(
            generation,
            seconds,
            float(args.refresh_seconds),
            active,
        )
        if rc:
            child_failures+=1

    print(
        "[LIVE_MONEY_DRIVER_DONE] generations=%d child_failures=%d active_pairs=%d"
        %(generation,child_failures,len(active.get("pairs") or [])),
        flush=True,
    )
    return 0 if child_failures==0 else 1


if __name__=="__main__":
    raise SystemExit(main())
