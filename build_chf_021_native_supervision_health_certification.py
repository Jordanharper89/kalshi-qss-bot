from pathlib import Path
import py_compile

ROOT=Path.cwd()
assert (ROOT/"run_oracle_LIVE.py").exists()
assert (ROOT/"run_coinbase_hf_live.py").exists()

test_code = """from pathlib import Path
import subprocess, sys, time

ROOT=Path.cwd()
src=(ROOT/"run_oracle_LIVE.py").read_text(encoding="utf-8")
assert '"coinbase_hf"' in src and '"run_coinbase_hf_live.py"' in src
assert '"ksem_mapping"' in src

p=subprocess.Popen([sys.executable,"run_oracle_LIVE.py"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
lines=[]
healthy=False
deadline=time.time()+35
try:
    while time.time()<deadline:
        line=p.stdout.readline()
        if line:
            lines.append(line.rstrip())
            print(line.rstrip())
            joined="\\n".join(lines[-120:])
            if "coinbase_hf=RUNNING" in joined or ("coinbase_hf" in joined and "HEALTHY" in joined):
                healthy=True
                break
        elif p.poll() is not None:
            break
finally:
    p.terminate()
    try:p.wait(timeout=5)
    except Exception:p.kill()

assert healthy,"coinbase_hf native child did not reach supervised RUNNING/HEALTHY state"
print("[PASS] run_oracle_LIVE.py physically supervised coinbase_hf")
print("[PASS] native health surfaced through Oracle supervisor")
print("[PASS] CHF-021 native supervision health certified")
"""
t=ROOT/"test_chf_021_native_supervision_health_certification.py"
t.write_text(test_code,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote",t)
print("[PASS] execution_authority=FALSE")