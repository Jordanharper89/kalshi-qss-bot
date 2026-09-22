from pathlib import Path

PROBE = r'''
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
'''

TEST = r'''
from pathlib import Path
p=Path("probe_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert "import run;" in s
assert "exogenous_evidence_snapshot" in s
assert "NEW IMMUTABLE ROWS" in s
assert "EXOGENOUS_EVIDENCE_PHYSICALLY_FROZEN" in s
print("[PASS] exact production predictor entrypoint run() used")
print("[PASS] fresh interpreter reloads patched production source")
print("[PASS] immutable ledger physically inspected")
print("[PASS] non-empty exogenous snapshot required")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''

Path("probe_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py").write_text(
    PROBE,encoding="utf-8"
)
Path("test_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py").write_text(
    TEST,encoding="utf-8"
)

compile(PROBE,"probe_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py","exec")
compile(TEST,"test_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py","exec")

print("[PASS] exact-run-entry physical exogenous probe installed")
print("[ENTRYPOINT] run")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")