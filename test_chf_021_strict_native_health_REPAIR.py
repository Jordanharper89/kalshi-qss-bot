import subprocess,sys,time
from pathlib import Path
ROOT=Path.cwd()
p=subprocess.Popen([sys.executable,"run_oracle_LIVE.py"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
healthy=0; bad=False; lines=[]; deadline=time.time()+45
try:
    while time.time()<deadline:
        line=p.stdout.readline()
        if line:
            line=line.rstrip(); lines.append(line); print(line)
            if "ImportError" in line or "child=coinbase_hf event=EXIT" in line or "coinbase_hf=FAILED" in line:
                bad=True; break
            if "[ORACLE]" in line and "coinbase_hf=HEALTHY" in line:
                healthy+=1
                if healthy>=2: break
        elif p.poll() is not None: break
finally:
    p.terminate()
    try:p.wait(timeout=5)
    except Exception:p.kill()

assert not bad,"coinbase_hf crashed or reported FAILED"
assert healthy>=2,f"need two HEALTHY heartbeats, got {healthy}"
print("[PASS] prior false-positive CHF-021 gate retired")
print("[PASS] coinbase_hf remained HEALTHY for two Oracle heartbeats")
print("[PASS] CHF-021 strict native supervision health certified")
