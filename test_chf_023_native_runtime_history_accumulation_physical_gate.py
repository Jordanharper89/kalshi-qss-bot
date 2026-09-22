from pathlib import Path
import subprocess, sys, time, json

ROOT=Path.cwd()
hist=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
before=hist.stat().st_size if hist.exists() else 0

p=subprocess.Popen([sys.executable,"run_oracle_LIVE.py"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
deadline=time.time()+80
try:
    while time.time()<deadline:
        line=p.stdout.readline()
        if line:
            print(line.rstrip())
        if hist.exists() and hist.stat().st_size>before:
            break
        if p.poll() is not None:
            break
finally:
    p.terminate()
    try:p.wait(timeout=5)
    except Exception:p.kill()

after=hist.stat().st_size if hist.exists() else 0
assert after>before,f"historical archive did not grow: before={before} after={after}"
rows=[json.loads(x) for x in hist.read_text(encoding="utf-8").splitlines() if x.strip()]
products={r.get("product_id") for r in rows}
assert {"BTC-USD","ETH-USD","SOL-USD"}.issubset(products)
assert all(r.get("no_future_leakage") is True for r in rows[-min(20,len(rows)):])
print("[HISTORY_BYTES]",before,"->",after)
print("[PASS] native Oracle runtime accumulated CHF historical windows")
print("[PASS] BTC/ETH/SOL present in durable history")
print("[PASS] no-future-leakage retained")
print("[PASS] CHF-023 physical native-runtime history accumulation certified")
