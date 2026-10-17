from pathlib import Path
import ast

ROOT=Path.cwd()
RUNTIME=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"
CP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"
TEST=ROOT/"test_restore_last_positive_money_path.py"

for p in (RUNTIME,LM,CP25):
    if not p.is_file():
        raise RuntimeError("REQUIRED_TARGET_MISSING:"+str(p))

rs=RUNTIME.read_text(encoding="utf-8")
lms=LM.read_text(encoding="utf-8")
cps=CP25.read_text(encoding="utf-8")

tree=ast.parse(rs)
nodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

serve_node=nodes.get("serve_canonical")
if serve_node is None:
    raise RuntimeError("SERVE_CANONICAL_NOT_FOUND")

lines=rs.splitlines(keepends=True)
starts=[]
pos=0
for line in lines:
    starts.append(pos); pos+=len(line)

def node_span(node):
    a=starts[node.lineno-1]
    b=starts[node.end_lineno-1]+len(lines[node.end_lineno-1])
    return a,b

edits=[]
a,b=node_span(serve_node)
edits.append((a,b,'async def serve_canonical(\n    state,\n    seconds,\n    lane\n):\n\n    addresses=list(\n        state.get(\n            "addresses"\n        )\n        or []\n    )\n\n    shards=(\n        persistent.m\n        ._shards(\n            addresses\n        )\n    )\n\n    counters={\n        "acks":0,\n        "notifications":0,\n        "priced_events":0,\n        "observed_only_events":0,\n        "signals":0,\n        "event_errors":0,\n        "queue_drops":0,\n        "connections":0,\n        "reconnects":0,\n        "rate_limit_disconnects":0,\n        "last_ws_error":None,\n        "lat":[],\n        "best":None,\n    }\n\n    queue=asyncio.Queue(\n        maxsize=persistent.QUEUE_MAX\n    )\n\n    stop=asyncio.Event()\n\n    workers=[\n        asyncio.create_task(\n            persistent._worker(\n                i,\n                shard,\n                queue,\n                counters,\n                stop,\n            )\n        )\n        for i,shard\n        in enumerate(shards)\n    ]\n\n    print(\n        "[CANONICAL_WS] "\n        "accounts=%d shards=%d "\n        "ready_pairs=%d"\n        %(\n            len(addresses),\n            len(shards),\n            len(\n                METEORA_TEMPLATES\n            ),\n        ),\n        flush=True,\n    )\n\n    started=time.monotonic()\n    last_hb=started\n    last_n=0\n\n    try:\n\n        while not stop.is_set():\n\n            if (\n                time.monotonic()\n                -started\n                >=float(seconds)\n            ):\n                break\n\n            try:\n\n                ev=await asyncio.wait_for(\n                    queue.get(),\n                    timeout=.25,\n                )\n\n                process_event(\n                    state,\n                    ev,\n                    counters,\n                    lane,\n                )\n\n            except asyncio.TimeoutError:\n                pass\n\n            now=time.monotonic()\n\n            if now-last_hb>=15.0:\n\n                span=max(\n                    .001,\n                    now-last_hb\n                )\n\n                eps=(\n                    counters[\n                        "notifications"\n                    ]\n                    -last_n\n                )/span\n\n                print(\n                    "[CANONICAL_HEARTBEAT] "\n                    "uptime_s=%d "\n                    "notifications=%d "\n                    "eps=%.2f "\n                    "priced_events=%d "\n                    "submitted=%d "\n                    "replaced=%d "\n                    "processed=%d "\n                    "positive=%d "\n                    "scan_replaced=%d "\n                    "reconnects=%d "\n                    "rate_limits=%d"\n                    %(\n                        int(\n                            now-started\n                        ),\n                        counters[\n                            "notifications"\n                        ],\n                        eps,\n                        counters[\n                            "priced_events"\n                        ],\n                        lane.submitted,\n                        lane.replaced,\n                        lane.processed,\n                        lane.positive,\n                        lane.scan_replaced,\n                        counters[\n                            "reconnects"\n                        ],\n                        counters[\n                            "rate_limit_disconnects"\n                        ],\n                    ),\n                    flush=True,\n                )\n\n                last_hb=now\n\n                last_n=counters[\n                    "notifications"\n                ]\n\n    finally:\n\n        stop.set()\n\n        for worker in workers:\n            worker.cancel()\n\n        await asyncio.gather(\n            *workers,\n            return_exceptions=True\n        )\n\n    return counters\n'.strip()+"\n\n"))

helper=nodes.get("build_universal_subscription_windows")
if helper is not None:
    a,b=node_span(helper)
    edits.append((a,b,""))

edits.sort(key=lambda x:x[0],reverse=True)
newrs=rs
for a,b,repl in edits:
    newrs=newrs[:a]+repl+newrs[b:]

# Restore CP25 to the bounded HOT book owner.
if '"live_hot_book.json"' not in cps:
    old='"capacity_aware_warm_universe.json"'
    if old not in cps:
        raise RuntimeError("CP25_MANIFEST_SEAM_NOT_FOUND")
    cps=cps.replace(old,'"live_hot_book.json"',1)

# Restore the pre-rotation feed-freeze declaration.
lms=lms.replace(
    'print("[FEED_FREEZE] false universal_rotation=True",flush=True)',
    'print("[FEED_FREEZE] true",flush=True)',
)

# Refuse to write unless this is the known positive-capable fixed-slice shape.
required=[
    "[CANONICAL_WS]",
    "persistent._worker(",
    "METEORA_TEMPLATES",
    '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)',
]
for marker in required:
    if marker not in newrs:
        raise RuntimeError("ROLLBACK_POSTCONDITION_MISSING:"+marker)

for forbidden in (
    "[UNIVERSAL_ROTATION]",
    "[UNIVERSAL_SURVEILLANCE]",
    "def build_universal_subscription_windows",
):
    if forbidden in newrs:
        raise RuntimeError("ROTATION_PATH_REMAINS:"+forbidden)

if "_atomic_write(CAPACITY,hot)" in lms:
    raise RuntimeError("DESTRUCTIVE_CAPACITY_OVERWRITE_REGRESSION")

ast.parse(newrs); ast.parse(lms); ast.parse(cps)

RUNTIME.write_text(newrs,encoding="utf-8")
LM.write_text(lms,encoding="utf-8")
CP25.write_text(cps,encoding="utf-8")

TEST_CODE='from pathlib import Path\nimport ast\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\n\nROOT=Path.cwd()\nR=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"\nLM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"\nCP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"\n\nrs=R.read_text(encoding="utf-8")\nlms=LM.read_text(encoding="utf-8")\ncps=CP25.read_text(encoding="utf-8")\nast.parse(rs); ast.parse(lms); ast.parse(cps)\n\nassert "async def serve_canonical(" in rs\nassert "[CANONICAL_WS]" in rs\nassert "[UNIVERSAL_ROTATION]" not in rs\nassert "[UNIVERSAL_SURVEILLANCE]" not in rs\nassert "def build_universal_subscription_windows" not in rs\nassert \'"live_hot_book.json"\' in cps\nassert \'print("[FEED_FREEZE] true",flush=True)\' in lms\nassert "_atomic_write(CAPACITY,hot)" not in lms\nassert \'"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)\' in rs\nassert \'METEORA_TEMPLATES[token+"|"+pool]\' in rs\nassert "sendTransaction" not in rs\n\nprint("[PASS] fixed HOT-book canonical scanner restored")\nprint("[PASS] universal rotation path removed")\nprint("[PASS] CP25 consumes live_hot_book again")\nprint("[PASS] exact-pair identity preserved")\nprint("[PASS] universal capacity remains non-destructively preserved")\nprint("[PASS] broadcast remains disabled")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] LAST POSITIVE MONEY PATH RESTORATION")
print("[SCANNER] fixed bounded HOT-book canonical websocket path restored")
print("[CP25] live_hot_book.json restored as runtime slice")
print("[PERSISTENT] canonical workers preserved")
print("[IDENTITY] token|meteora_pool preserved")
print("[CAPACITY] universal master preserved outside execution slice")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
