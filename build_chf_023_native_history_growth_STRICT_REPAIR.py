from pathlib import Path
import py_compile

ROOT=Path.cwd()
assert (ROOT/"run_oracle_LIVE.py").exists()
assert (ROOT/"run_coinbase_hf_live.py").exists()

TEST=r"""from pathlib import Path
import subprocess,sys,time
ROOT=Path.cwd(); hist=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
before=hist.stat().st_size if hist.exists() else 0
p=subprocess.Popen([sys.executable,"run_oracle_LIVE.py"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
healthy=0; grew=False; bad=False; deadline=time.time()+70
try:
    while time.time()<deadline:
        line=p.stdout.readline()
        if line:
            line=line.rstrip(); print(line)
            if "ImportError" in line or "child=coinbase_hf event=EXIT" in line or "coinbase_hf=FAILED" in line:
                bad=True; break
            if "[ORACLE]" in line and "coinbase_hf=HEALTHY" in line: healthy+=1
            if hist.exists() and hist.stat().st_size>before:
                grew=True
                if healthy>=2: break
        elif p.poll() is not None: break
finally:
    p.terminate()
    try:p.wait(timeout=5)
    except Exception:p.kill()
after=hist.stat().st_size if hist.exists() else 0
print("[HISTORY_BYTES]",before,"->",after)
assert not bad,"coinbase_hf crashed during native runtime"
assert healthy>=2,f"need two healthy heartbeats, got {healthy}"
assert grew and after>before,"historical archive did not grow under native Oracle runtime"
print("[PASS] prior non-growing CHF-023 gate retired")
print("[PASS] coinbase_hf stayed healthy while history grew")
print("[PASS] CHF-023 strict native history accumulation certified")
"""
t=ROOT/"test_chf_023_native_history_growth_STRICT_REPAIR.py"
t.write_text(TEST,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote",t)
print("[PASS] execution_authority=FALSE")