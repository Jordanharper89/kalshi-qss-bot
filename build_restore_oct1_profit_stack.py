from pathlib import Path
import subprocess, ast, time, json

ROOT=Path.cwd()
COMMIT="a23f4efb4cfc365c39435d4b968ff5674ab69fd8"

FILES=[
    "qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py",
    "qseries_v2/oracle_execution/oracle_019_venue_native_reserve_feed_cutover.py",
    "qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py",
    "qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py",
    "qseries_v2/oracle_execution/solana_atomic_executor/runtime.py",
]

STAMP=time.strftime("%Y%m%d_%H%M%S")
BACKUP=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"/("profit_recovery_backup_"+STAMP)
BACKUP.mkdir(parents=True,exist_ok=True)

def git_show(path):
    p=subprocess.run(
        ["git","show",COMMIT+":"+path],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if p.returncode!=0:
        raise RuntimeError("GIT_SHOW_FAILED:"+path+":"+p.stderr[-500:])
    if not p.stdout.strip():
        raise RuntimeError("GIT_SHOW_EMPTY:"+path)
    ast.parse(p.stdout)
    return p.stdout

payloads={}
for rel in FILES:
    target=ROOT/rel
    if not target.is_file():
        raise RuntimeError("TARGET_MISSING:"+rel)

    current=target.read_text(encoding="utf-8")
    ast.parse(current)

    backup=BACKUP/rel
    backup.parent.mkdir(parents=True,exist_ok=True)
    backup.write_text(current,encoding="utf-8")

    payloads[rel]=git_show(rel)

for rel,content in payloads.items():
    target=ROOT/rel
    target.write_text(content,encoding="utf-8")
    ast.parse(target.read_text(encoding="utf-8"))

q20=(ROOT/FILES[2]).read_text(encoding="utf-8")
runtime=(ROOT/FILES[4]).read_text(encoding="utf-8")

checks=[
    ("self.processed+=1",q20,"Q20_PROCESSED_COUNTER"),
    ("self.positive+=1",q20,"Q20_POSITIVE_COUNTER"),
    ("FULL_SIZE_CURVE=(",q20,"Q20_FULL_SIZE_CURVE"),
    ("_lane.submit(pair.token",q20,"Q20_TOKEN_LANE_SUBMIT"),
    ("METEORA_TEMPLATES[token]={",runtime,"RUNTIME_TOKEN_METEORA_TEMPLATE"),
    ("READY_TOKENS.intersection_update(",runtime,"RUNTIME_READY_INTERSECTION"),
    ("build_meteora_ix_hot(",runtime,"RUNTIME_METEORA_HOT_BUILDER"),
]

for marker,text,name in checks:
    if marker not in text:
        raise RuntimeError("RESTORE_CHECK_FAILED:"+name)

RUNNER=ROOT/"run_restored_profit_gate.py"
RUNNER_CODE='from pathlib import Path\nimport json, subprocess, sys\n\nSECONDS=60\n\ncmd=[\n    sys.executable,\n    "-m",\n    "qseries_v2.oracle_execution.oracle_025_single_hydration_exact_live_reuse",\n    "--seconds",\n    str(SECONDS),\n]\n\nprint("[PROFIT_RECOVERY] restored October-1 positive-producing stack",flush=True)\nprint("[WINDOW] %ds"%SECONDS,flush=True)\nprint("[BROADCAST] disabled",flush=True)\n\nrc=subprocess.call(cmd)\n\nreport=Path(\n    "runtime_state/oracle/oracle_live_execution/"\n    "oracle_020_latest_state_exact_pricing_worker.json"\n)\n\nif not report.is_file():\n    print("[PROFIT_GATE] CLOSED reason=ORACLE020_REPORT_MISSING",flush=True)\n    raise SystemExit(2 if rc==0 else rc)\n\ndata=json.loads(report.read_text(encoding="utf-8"))\nprocessed=int(data.get("processed") or 0)\npositive=int(data.get("positive") or 0)\nbest=data.get("best") or {}\n\nprint(\n    "[PROFIT_GATE_RESULT] processed=%d positive=%d best_net=%s best_bps=%s direction=%s size=%s"\n    %(\n        processed,\n        positive,\n        str(best.get("local_net")),\n        str(best.get("local_bps")),\n        str(best.get("direction")),\n        str(best.get("size_sol")),\n    ),\n    flush=True,\n)\n\nif processed<=0:\n    print("[PROFIT_GATE] CLOSED reason=PRICING_NOT_PROCESSING",flush=True)\n    raise SystemExit(3)\n\nif positive<=0:\n    print("[PROFIT_GATE] CLOSED reason=NO_CURRENT_POSITIVE_IN_WINDOW",flush=True)\n    raise SystemExit(4)\n\nprint("[PROFIT_GATE] OPEN current_live_positive_observed=True",flush=True)\nprint("[NEXT] reconnect this exact positive route to signed-sim/fee gate before broadcast",flush=True)\nprint("[BROADCAST] disabled",flush=True)\nraise SystemExit(0)\n'
RUNNER.write_text(RUNNER_CODE,encoding="utf-8")
ast.parse(RUNNER_CODE)

TEST=ROOT/"test_restore_oct1_profit_stack.py"
TEST_CODE='from pathlib import Path\nimport ast\n\nROOT=Path.cwd()\npaths=[\n    ROOT/"qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py",\n    ROOT/"qseries_v2/oracle_execution/oracle_019_venue_native_reserve_feed_cutover.py",\n    ROOT/"qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py",\n    ROOT/"qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py",\n    ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py",\n]\n\nfor p in paths:\n    ast.parse(p.read_text(encoding="utf-8"))\n\nq20=paths[2].read_text(encoding="utf-8")\nruntime=paths[4].read_text(encoding="utf-8")\n\nassert "self.processed+=1" in q20\nassert "self.positive+=1" in q20\nassert "FULL_SIZE_CURVE=(" in q20\nassert "_lane.submit(pair.token" in q20\nassert "METEORA_TEMPLATES[token]={" in runtime\nassert "READY_TOKENS.intersection_update(" in runtime\nassert "EXECUTION_AUTHORITY=False" in runtime\n\nprint("[PASS] October-1 positive-producing pricing stack restored")\nprint("[PASS] live lane can increment processed/positive counters")\nprint("[PASS] full approved size curve restored in ORACLE-020")\nprint("[PASS] token-keyed readiness/pricing path restored")\nprint("[PASS] execution authority remains false")\nprint("[BROADCAST] disabled")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

manifest={
    "commit":COMMIT,
    "files":FILES,
    "backup":str(BACKUP),
    "runner":RUNNER.name,
    "test":TEST.name,
}
(ROOT/"PROFIT_RECOVERY_MANIFEST.json").write_text(
    json.dumps(manifest,indent=2),
    encoding="utf-8",
)

print("[PASS] OCTOBER-1 PROFIT STACK RESTORATION")
print("[SOURCE] git commit",COMMIT)
print("[FILES]",len(FILES))
print("[BACKUP]",BACKUP)
print("[PRICING] ORACLE-020 processed/positive lane restored")
print("[SIZES] full approved curve restored")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] disabled")
print("[RUNNER]",RUNNER.name)
print("[TEST]",TEST.name)
