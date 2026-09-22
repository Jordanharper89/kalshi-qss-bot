import subprocess, sys
probe = """from qseries_v2.oracle_source_network.acquisition.nhl_official_live import acquire_nhl_schedule
x=acquire_nhl_schedule(8)
print(f"[PHYSICAL] NHL bytes={len(x['body'])} markers={x['markers']}")
assert x["provider"]=="nhl_official" and x["league"]=="NHL"
assert x["source_authority"]=="official_league"
assert len(x["payload_sha256"])==64 and x["read_only"] and not x["execution_authority"]
assert all(x["markers"].values())
print("[PASS] NHL official physical acquisition completed")"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=15)
except subprocess.TimeoutExpired:
    raise AssertionError("NHL acquisition exceeded hard 15-second wall-clock gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"NHL physical probe failed rc={p.returncode}"
print("[PASS] OSN-021 NHL official physical acquisition certified")
