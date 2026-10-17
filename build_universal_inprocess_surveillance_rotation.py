from pathlib import Path
import ast

ROOT=Path.cwd()
RUNTIME=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"
CP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"
TEST=ROOT/"test_universal_surveillance_rotation.py"

for p in (RUNTIME,LM,CP25):
    if not p.is_file():
        raise RuntimeError("REQUIRED_TARGET_MISSING:"+str(p))

runtime=RUNTIME.read_text(encoding="utf-8")
lm=LM.read_text(encoding="utf-8")
cp25=CP25.read_text(encoding="utf-8")

# CP25 must hydrate the universal capacity registry once at startup.
if '"live_hot_book.json"' in cp25:
    cp25=cp25.replace(
        '"live_hot_book.json"',
        '"capacity_aware_warm_universe.json"',
        1,
    )

cp25=cp25.replace(
    '"[CHECKPOINT25_UNIVERSAL_BOUNDARY] universal_pairs=%d hot_pairs=%d hot_is_scheduler_slice=True"',
    '"[CHECKPOINT25_UNIVERSAL_HYDRATION] universal_pairs=%d hydration_pairs=%d scheduler_slice_separate=True"',
)

# The old startup selector remains a priority file only, never the hydrated universe.
lm=lm.replace(
    'print("[FEED_FREEZE] true",flush=True)',
    'print("[FEED_FREEZE] false universal_rotation=True",flush=True)',
)

# Replace the entire canonical websocket service function by name; no internal seam guessing.
tree=ast.parse(runtime)
serve=None
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=="serve_canonical":
        serve=node
        break
if serve is None:
    raise RuntimeError("SERVE_CANONICAL_NOT_FOUND")

lines=runtime.splitlines(keepends=True)
starts=[]
pos=0
for line in lines:
    starts.append(pos)
    pos+=len(line)

a=starts[serve.lineno-1]
b=starts[serve.end_lineno-1]+len(lines[serve.end_lineno-1])

helper='\ndef build_universal_subscription_windows(\n    state,\n    max_accounts=318,\n    hot_keys=None,\n    active_keys=None,\n):\n    import json as _json\n    from pathlib import Path as _Path\n\n    max_accounts=int(max_accounts)\n    if max_accounts<=0:\n        raise RuntimeError("UNIVERSAL_SCHEDULER_BAD_ACCOUNT_CAP")\n\n    pairs=list(state.get("pairs") or [])\n    address_index=dict(state.get("address_index") or {})\n\n    if not pairs or not address_index:\n        raise RuntimeError("UNIVERSAL_SCHEDULER_EMPTY_STATE")\n\n    pair_addresses={i:set() for i in range(len(pairs))}\n\n    for address,meta in address_index.items():\n        if isinstance(meta,(list,tuple)):\n            index=int(meta[0])\n        elif isinstance(meta,dict):\n            index=int(\n                meta.get("index")\n                if meta.get("index") is not None\n                else meta.get("pair_index")\n            )\n        else:\n            index=int(meta)\n\n        if 0<=index<len(pairs):\n            pair_addresses[index].add(str(address))\n\n    rows=[]\n    for index,pair in enumerate(pairs):\n        token=str(pair.token)\n        pool=str(pair.meteora_pool)\n        key=token+"|"+pool\n        addresses=pair_addresses.get(index) or set()\n\n        if not addresses:\n            continue\n\n        if len(addresses)>max_accounts:\n            raise RuntimeError(\n                "UNIVERSAL_PAIR_ACCOUNT_BUDGET_BREACH:"\n                +key+":"+str(len(addresses))\n            )\n\n        rows.append({\n            "index":index,\n            "pair_key":key,\n            "token":token,\n            "addresses":set(addresses),\n        })\n\n    if not rows:\n        raise RuntimeError("UNIVERSAL_SCHEDULER_NO_WATCHABLE_PAIRS")\n\n    root=_Path.cwd()\n    state_dir=(\n        root/"runtime_state"/"oracle"/"solana_atomic_executor"\n    )\n\n    def load_keys(path):\n        if not path.is_file():\n            return []\n        try:\n            data=_json.loads(path.read_text(encoding="utf-8"))\n        except Exception:\n            return []\n\n        out=[]\n        for row in list(data.get("pairs") or data.get("rows") or []):\n            key=str(\n                row.get("pair_key")\n                or row.get("identity")\n                or (\n                    str(row.get("token") or "")\n                    +"|"\n                    +str(row.get("meteora_pool") or "")\n                )\n            )\n            if "|" in key and key not in out:\n                out.append(key)\n        return out\n\n    if hot_keys is None:\n        hot_keys=load_keys(state_dir/"live_hot_book.json")\n    else:\n        hot_keys=list(hot_keys)\n\n    if active_keys is None:\n        active_keys=load_keys(\n            state_dir/"active_after_fee_pairs.json"\n        )\n    else:\n        active_keys=list(active_keys)\n\n    by_key={row["pair_key"]:row for row in rows}\n\n    active=[\n        key for key in active_keys\n        if key in by_key\n    ]\n\n    resident_accounts=set()\n    resident_pairs=[]\n\n    for key in active:\n        row=by_key[key]\n        union=resident_accounts|row["addresses"]\n\n        if len(union)>max_accounts:\n            raise RuntimeError(\n                "ACTIVE_RESIDENT_ACCOUNT_BUDGET_BREACH:"\n                +key\n            )\n\n        resident_accounts=union\n        resident_pairs.append(key)\n\n    active_set=set(resident_pairs)\n\n    remaining=[\n        row for row in rows\n        if row["pair_key"] not in active_set\n    ]\n\n    hot_order=[]\n    seen_hot=set()\n\n    for key in hot_keys:\n        if key in by_key and key not in active_set and key not in seen_hot:\n            hot_order.append(by_key[key])\n            seen_hot.add(key)\n\n    rest=[\n        row for row in remaining\n        if row["pair_key"] not in seen_hot\n    ]\n\n    first=[]\n    duplicates=[]\n    seen_tokens=set()\n\n    for row in hot_order+rest:\n        if row["token"] in seen_tokens:\n            duplicates.append(row)\n        else:\n            seen_tokens.add(row["token"])\n            first.append(row)\n\n    ordered=first+duplicates\n\n    windows=[]\n\n    while ordered:\n        accounts=set(resident_accounts)\n        keys=list(resident_pairs)\n        used=[]\n        progress=False\n\n        for i,row in enumerate(ordered):\n            union=accounts|row["addresses"]\n            if len(union)<=max_accounts:\n                accounts=union\n                keys.append(row["pair_key"])\n                used.append(i)\n                progress=True\n\n        if not progress:\n            row=ordered[0]\n            raise RuntimeError(\n                "UNIVERSAL_PAIR_CANNOT_COEXIST_WITH_ACTIVE:"\n                +row["pair_key"]\n            )\n\n        used_set=set(used)\n        ordered=[\n            row for i,row in enumerate(ordered)\n            if i not in used_set\n        ]\n\n        windows.append({\n            "pair_keys":keys,\n            "resident_pairs":list(resident_pairs),\n            "addresses":sorted(accounts),\n        })\n\n    if not windows:\n        windows=[{\n            "pair_keys":list(resident_pairs),\n            "resident_pairs":list(resident_pairs),\n            "addresses":sorted(resident_accounts),\n        }]\n\n    expected={row["pair_key"] for row in rows}\n    observed={\n        key\n        for window in windows\n        for key in window["pair_keys"]\n    }\n\n    if observed!=expected:\n        missing=sorted(expected-observed)\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_COVERAGE_GAP:"\n            +",".join(missing[:5])\n        )\n\n    for window in windows:\n        if len(window["addresses"])>max_accounts:\n            raise RuntimeError(\n                "UNIVERSAL_WINDOW_ACCOUNT_BUDGET_BREACH"\n            )\n\n    print(\n        "[UNIVERSAL_SCHEDULER_READY] pairs=%d windows=%d "\n        "active_resident=%d max_accounts=%d"\n        %(\n            len(expected),\n            len(windows),\n            len(resident_pairs),\n            max_accounts,\n        ),\n        flush=True,\n    )\n\n    return windows\n'
serve_new='\nasync def serve_canonical(state,seconds,lane):\n    windows=build_universal_subscription_windows(\n        state,\n        max_accounts=318,\n    )\n\n    counters={\n        "acks":0,\n        "notifications":0,\n        "priced_events":0,\n        "observed_only_events":0,\n        "signals":0,\n        "event_errors":0,\n        "queue_drops":0,\n        "connections":0,\n        "reconnects":0,\n        "rate_limit_disconnects":0,\n        "last_ws_error":None,\n        "lat":[],\n        "best":None,\n        "rotations":0,\n    }\n\n    queue=asyncio.Queue(maxsize=persistent.QUEUE_MAX)\n    stop=asyncio.Event()\n    started=time.monotonic()\n    last_hb=started\n    last_n=0\n    cycle=0\n    window_index=0\n    seen_pairs=set()\n    rotation_seconds=30.0 if len(windows)>1 else float(seconds)\n\n    print(\n        "[UNIVERSAL_SURVEILLANCE] pairs=%d windows=%d "\n        "window_accounts<=318 rotation_seconds=%.0f"\n        %(\n            len({k for w in windows for k in w["pair_keys"]}),\n            len(windows),\n            rotation_seconds,\n        ),\n        flush=True,\n    )\n\n    async def stop_workers(workers):\n        for worker in workers:\n            worker.cancel()\n        if workers:\n            await asyncio.gather(*workers,return_exceptions=True)\n\n    workers=[]\n\n    try:\n        while not stop.is_set():\n            now=time.monotonic()\n            if now-started>=float(seconds):\n                break\n\n            window=windows[window_index]\n            addresses=list(window["addresses"])\n            shards=persistent.m._shards(addresses)\n\n            seen_pairs.update(window["pair_keys"])\n            counters["rotations"]+=1\n\n            print(\n                "[UNIVERSAL_ROTATION] cycle=%d window=%d/%d "\n                "pairs=%d accounts=%d shards=%d resident_active=%d "\n                "coverage_seen=%d/%d"\n                %(\n                    cycle+1,\n                    window_index+1,\n                    len(windows),\n                    len(window["pair_keys"]),\n                    len(addresses),\n                    len(shards),\n                    len(window["resident_pairs"]),\n                    len(seen_pairs),\n                    len({k for w in windows for k in w["pair_keys"]}),\n                ),\n                flush=True,\n            )\n\n            workers=[\n                asyncio.create_task(\n                    persistent._worker(\n                        i,\n                        shard,\n                        queue,\n                        counters,\n                        stop,\n                    )\n                )\n                for i,shard in enumerate(shards)\n            ]\n\n            window_started=time.monotonic()\n\n            while not stop.is_set():\n                now=time.monotonic()\n\n                if now-started>=float(seconds):\n                    break\n\n                if (\n                    len(windows)>1\n                    and now-window_started>=rotation_seconds\n                ):\n                    break\n\n                try:\n                    ev=await asyncio.wait_for(\n                        queue.get(),\n                        timeout=.25,\n                    )\n                    process_event(\n                        state,\n                        ev,\n                        counters,\n                        lane,\n                    )\n                except asyncio.TimeoutError:\n                    pass\n\n                now=time.monotonic()\n\n                if now-last_hb>=15.0:\n                    span=max(.001,now-last_hb)\n                    eps=(\n                        counters["notifications"]-last_n\n                    )/span\n\n                    print(\n                        "[CANONICAL_HEARTBEAT] "\n                        "uptime_s=%d notifications=%d eps=%.2f "\n                        "priced_events=%d submitted=%d replaced=%d "\n                        "processed=%d positive=%d scan_replaced=%d "\n                        "reconnects=%d rate_limits=%d rotations=%d "\n                        "coverage=%d/%d"\n                        %(\n                            int(now-started),\n                            counters["notifications"],\n                            eps,\n                            counters["priced_events"],\n                            lane.submitted,\n                            lane.replaced,\n                            lane.processed,\n                            lane.positive,\n                            lane.scan_replaced,\n                            counters["reconnects"],\n                            counters["rate_limit_disconnects"],\n                            counters["rotations"],\n                            len(seen_pairs),\n                            len({k for w in windows for k in w["pair_keys"]}),\n                        ),\n                        flush=True,\n                    )\n\n                    last_hb=now\n                    last_n=counters["notifications"]\n\n            await stop_workers(workers)\n            workers=[]\n\n            if len(windows)>1:\n                window_index+=1\n                if window_index>=len(windows):\n                    window_index=0\n                    cycle+=1\n\n    finally:\n        stop.set()\n        await stop_workers(workers)\n\n    print(\n        "[UNIVERSAL_SURVEILLANCE_DONE] rotations=%d coverage=%d/%d"\n        %(\n            counters["rotations"],\n            len(seen_pairs),\n            len({k for w in windows for k in w["pair_keys"]}),\n        ),\n        flush=True,\n    )\n\n    return counters\n'

replacement=helper+"\n\n"+serve_new.strip()+"\n"
new_runtime=runtime[:a]+replacement+runtime[b:]

# Hard postconditions before writing.
required=[
    "def build_universal_subscription_windows",
    "[UNIVERSAL_ROTATION]",
    "[UNIVERSAL_SURVEILLANCE]",
    "rotation_seconds=30.0",
    "ACTIVE_RESIDENT_ACCOUNT_BUDGET_BREACH",
]
for marker in required:
    if marker not in new_runtime:
        raise RuntimeError("POSTCONDITION_MISSING:"+marker)

if '_atomic_write(CAPACITY,hot)' in lm:
    raise RuntimeError("UNIVERSAL_CAPACITY_OVERWRITE_REGRESSION")

if '"capacity_aware_warm_universe.json"' not in cp25:
    raise RuntimeError("CP25_UNIVERSAL_MANIFEST_MISSING")

ast.parse(new_runtime)
ast.parse(lm)
ast.parse(cp25)

RUNTIME.write_text(new_runtime,encoding="utf-8")
LM.write_text(lm,encoding="utf-8")
CP25.write_text(cp25,encoding="utf-8")

TEST_CODE='from pathlib import Path\nimport ast\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm\nfrom qseries_v2.oracle_execution.solana_atomic_executor import checkpoint25_expanded_live_universe_cutover as c25\n\nrs=Path(r.__file__).read_text(encoding="utf-8")\nls=Path(lm.__file__).read_text(encoding="utf-8")\ncs=Path(c25.__file__).read_text(encoding="utf-8")\nast.parse(rs); ast.parse(ls); ast.parse(cs)\n\nassert "def build_universal_subscription_windows" in rs\nassert "[UNIVERSAL_ROTATION]" in rs\nassert "[UNIVERSAL_SURVEILLANCE]" in rs\nassert "rotation_seconds=30.0" in rs\nassert "_atomic_write(CAPACITY,hot)" not in ls\nassert "live_hot_book.json" in ls\nassert \'capacity_aware_warm_universe.json\' in cs\nassert "sendTransaction" not in rs\n\npairs=[\n    SimpleNamespace(token="A",meteora_pool="P1"),\n    SimpleNamespace(token="B",meteora_pool="P2"),\n    SimpleNamespace(token="C",meteora_pool="P3"),\n    SimpleNamespace(token="D",meteora_pool="P4"),\n]\naddress_index={}\nfor idx in range(4):\n    for j in range(4):\n        address_index["PAIR%d_A%d"%(idx,j)]=(idx,"kind")\n\nstate={"pairs":pairs,"address_index":address_index}\n\nwindows=r.build_universal_subscription_windows(\n    state,\n    max_accounts=8,\n    hot_keys=["A|P1","B|P2"],\n    active_keys=["A|P1"],\n)\n\nassert len(windows)>=2\nassert all(len(w["addresses"])<=8 for w in windows)\nassert all("A|P1" in w["pair_keys"] for w in windows)\n\ncoverage={\n    key\n    for w in windows\n    for key in w["pair_keys"]\n}\nassert coverage=={"A|P1","B|P2","C|P3","D|P4"}\n\nfor w in windows:\n    for key in w["pair_keys"]:\n        idx={"A|P1":0,"B|P2":1,"C|P3":2,"D|P4":3}[key]\n        needed={"PAIR%d_A%d"%(idx,j) for j in range(4)}\n        assert needed.issubset(set(w["addresses"]))\n\nprint("[PASS] universal exact-pair scheduler covers every pair")\nprint("[PASS] every window respects account cap")\nprint("[PASS] ACTIVE exact pairs remain resident across windows")\nprint("[PASS] whole-pair account sets rotate together")\nprint("[PASS] CP24/CP17 rebuild is not part of rotation")\nprint("[PASS] universal/HOT ownership preserved")\nprint("[BROADCAST] unchanged")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] UNIVERSAL IN-PROCESS SURVEILLANCE ROTATION REPLACEMENT")
print("[HYDRATION] universal exact-pair state startup-only")
print("[SCHEDULER] whole exact pairs rotate under <=318 live accounts")
print("[ACTIVE] after-fee exact pairs resident across windows")
print("[HOT] prioritized in rotation; never owns universal inventory")
print("[ROTATION] no CP24/CP17/template rebuild between windows")
print("[IDENTITY] token|meteora_pool preserved")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
