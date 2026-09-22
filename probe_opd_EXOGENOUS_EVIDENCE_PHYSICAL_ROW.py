
from pathlib import Path
import json, subprocess, sys, time

ROOT=Path.cwd().resolve()
LEDGER=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
PRED="qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor"
REV="EXOGENOUS_EVIDENCE_FREEZE_PHYSICAL_ROW_PROBE_V1"

def read_rows():
    out=[]
    if not LEDGER.exists(): return out
    with LEDGER.open("r",encoding="utf-8") as f:
        for line in f:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

before=read_rows()
before_ids={str(r.get("prediction_id")) for r in before if r.get("prediction_id")}
print("[LEDGER BEFORE]",len(before))

code = (
    "from pathlib import Path;"
    "from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor "
    "import run_prediction;"
    "r=run_prediction(root=Path.cwd().resolve());"
    "print('[FRESH RUN RESULT]',r)"
)
p=subprocess.run([sys.executable,"-c",code],cwd=str(ROOT),text=True,
                 capture_output=True,timeout=120)
print("[FRESH INTERPRETER EXIT]",p.returncode)
if p.stdout.strip(): print(p.stdout.strip())
if p.stderr.strip(): print("[STDERR]",p.stderr.strip())
if p.returncode!=0:
    raise SystemExit("[FAIL] fresh predictor invocation failed")

after=read_rows()
print("[LEDGER AFTER]",len(after))

new=[]
for r in after:
    pid=str(r.get("prediction_id") or "")
    if pid and pid not in before_ids:
        new.append(r)

candidates=new if new else after[-100:]
tag="NEW" if new else "RECENT_FALLBACK"
print("[ROWS INSPECTED]",len(candidates),"MODE=",tag)

with_field=[]
nonempty=[]
for r in candidates:
    if "exogenous_evidence_snapshot" in r:
        with_field.append(r)
        x=r.get("exogenous_evidence_snapshot")
        if isinstance(x,dict) and len(x)>0:
            nonempty.append(r)

print("[ROWS WITH SNAPSHOT FIELD]",len(with_field))
print("[ROWS WITH NONEMPTY SNAPSHOT]",len(nonempty))

if nonempty:
    r=nonempty[-1]
    snap=r["exogenous_evidence_snapshot"]
    print("[PASS] physical prediction row contains non-empty exogenous evidence snapshot")
    print("[PREDICTION_ID]",r.get("prediction_id"))
    print("[TICKER]",r.get("ticker"))
    print("[HORIZON]",r.get("horizon_seconds"))
    print("[SNAPSHOT KEYS]",len(snap))
    for k in list(sorted(snap))[:30]:
        v=snap[k]
        print("[EXO]",k,"=",str(v)[:180])
    print("[RESULT] EXOGENOUS_EVIDENCE_PHYSICALLY_FROZEN")
elif with_field:
    print("[FAIL] snapshot field is physically present but empty")
    print("[RESULT] PRODUCTION_STATE_HAS_NO_ELIGIBLE_RAW_EXOGENOUS_EVIDENCE_AT_PREDICTION_BOUNDARY")
    raise SystemExit(3)
else:
    print("[FAIL] no physical prediction row with exogenous_evidence_snapshot found")
    if not new:
        print("[NOTE] fresh predictor produced no new immutable ID; existing recent rows may predate cutover")
    print("[RESULT] EXOGENOUS_FREEZE_NOT_PHYSICALLY_PROVEN")
    raise SystemExit(4)

print("[NO EXECUTION/PUBLICATION] TRUE")
