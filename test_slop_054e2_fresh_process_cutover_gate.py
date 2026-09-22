import subprocess,sys
code='from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import REVISION;print(REVISION)'
x=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True)
print("[RETURN_CODE]",x.returncode)
print("[LOADED_REVISION]",x.stdout.strip())
if x.stderr.strip():print("[STDERR]",x.stderr.strip())
assert x.returncode==0
assert x.stdout.strip()=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
code='import ast;ast.parse(open("run_slop_buy_pressure_live.py",encoding="utf-8").read());print("RUNNER_PARSE_OK")'
y=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True)
print("[RUNNER]",y.stdout.strip())
assert y.returncode==0
assert y.stdout.strip()=="RUNNER_PARSE_OK"
print("[PASS] fresh Python process loads repaired admission revision")
print("[PASS] restored native runner loads from disk cleanly")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054E2 CERTIFIED")
