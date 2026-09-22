
from pathlib import Path
import json, subprocess, sys

ROOT=Path.cwd().resolve()
LEDGER=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"

def rows():
    out=[]
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            try: out.append(json.loads(line))
            except Exception: pass
    return out

before=rows()
before_ids={str(r.get("prediction_id")) for r in before if r.get("prediction_id")}
print("[LEDGER BEFORE]",len(before))

code=(
    "from pathlib import Path;"
    "from qseries_v2.oracle_predictive_discovery."
    "opd_live_full_evidence_fusion_predictor import run;"
    "r=run(root=Path.cwd().resolve());"
    "print('[FRESH RUN RESULT]',r)"
)

p=subprocess.run(
    [sys.executable,"-c",code],
    cwd=str(ROOT),
    text=True,
    capture_output=True,
    timeout=120
)

print("[FRESH INTERPRETER EXIT]",p.returncode)
if p.stdout.strip(): print(p.stdout.strip())
if p.stderr.strip(): print("[STDERR]",p.stderr.strip())
if p.returncode!=0:
    raise SystemExit("[FAIL] production run() invocation failed")

after=rows()
print("[LEDGER AFTER]",len(after))

new=[
    r for r in after
    if str(r.get("prediction_id") or "") not in before_ids
]

print("[NEW IMMUTABLE ROWS]",len(new))

inspect=new if new else after[-100:]
with_field=[
    r for r in inspect
    if "exogenous_evidence_snapshot" in r
]
nonempty=[
    r for r in with_field
    if isinstance(r.get("exogenous_evidence_snapshot"),dict)
    and len(r["exogenous_evidence_snapshot"])>0
]

print("[ROWS WITH SNAPSHOT FIELD]",len(with_field))
print("[ROWS WITH NONEMPTY SNAPSHOT]",len(nonempty))

if nonempty:
    r=nonempty[-1]
    snap=r["exogenous_evidence_snapshot"]
    print("[PASS] physical immutable prediction row carries raw exogenous evidence")
    print("[PREDICTION_ID]",r.get("prediction_id"))
    print("[TICKER]",r.get("ticker"))
    print("[HORIZON]",r.get("horizon_seconds"))
    print("[SNAPSHOT KEYS]",len(snap))
    for k in sorted(snap)[:40]:
        print("[EXO]",k,"=",str(snap[k])[:180])
    print("[RESULT] EXOGENOUS_EVIDENCE_PHYSICALLY_FROZEN")
elif with_field:
    print("[RESULT] SNAPSHOT_FIELD_PRESENT_BUT_EMPTY")
    raise SystemExit(3)
else:
    print("[RESULT] EXOGENOUS_FREEZE_NOT_PHYSICALLY_PROVEN")
    raise SystemExit(4)

print("[EXECUTION/PUBLICATION] FALSE/FALSE")
