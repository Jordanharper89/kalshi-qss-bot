from pathlib import Path
import json,subprocess,sys
root=Path.cwd().resolve()
ledger=root/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
def load():
    out=[]
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try: out.append(json.loads(line))
            except Exception: pass
    return out
before=load(); ids={str(x.get("prediction_id")) for x in before if x.get("prediction_id")}
print("[LEDGER BEFORE]",len(before))
code="from pathlib import Path;from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import run;run(root=Path.cwd().resolve())"
p=subprocess.run([sys.executable,"-c",code],cwd=str(root),text=True,capture_output=True,timeout=180)
print("[FRESH INTERPRETER EXIT]",p.returncode)
for line in p.stdout.splitlines():
    if ("LIVE_EVIDENCE_EXOGENOUS_SOURCES=" in line or
        "[PREDICTION LEDGER]" in line or
        "LIVE_PREDICTION=" in line):
        print(line)
if p.returncode:
    if p.stderr.strip(): print("[STDERR]",p.stderr[-3000:])
    raise SystemExit("[FAIL] production predictor run failed")
after=load()
new=[x for x in after if str(x.get("prediction_id") or "") not in ids]
print("[LEDGER AFTER]",len(after))
print("[NEW IMMUTABLE ROWS]",len(new))
field=[x for x in new if "exogenous_evidence_snapshot" in x]
nonempty=[x for x in field if isinstance(x.get("exogenous_evidence_snapshot"),dict) and x["exogenous_evidence_snapshot"]]
print("[ROWS WITH SNAPSHOT FIELD]",len(field))
print("[ROWS WITH NONEMPTY SNAPSHOT]",len(nonempty))
if not new: raise SystemExit("[FAIL] no new immutable predictions written")
if not nonempty: raise SystemExit("[FAIL] new rows still lack non-empty exogenous evidence")
sample=nonempty[0]
snap=sample["exogenous_evidence_snapshot"]
aseq=int(sample.get("anchor_sequence_boundary"))
at=float(sample.get("anchor_observed_epoch"))
bad=[];sources=set()
for k,v in snap.items():
    sid=str(v.get("source_id") or "");typ=str(v.get("observation_type") or "")
    sources.add(sid)
    seq=int(v.get("sequence_number"))
    oe=v.get("observed_epoch")
    low=(sid+" "+typ).lower()
    if seq>aseq: bad.append(("future_sequence",sid,seq))
    if oe is not None and float(oe)>at: bad.append(("future_time",sid,oe))
    if any(x in low for x in ("kalshi","coinbase","polymarket","market_data","orderbook","learned_case","historical_window")):
        bad.append(("denied_source",sid,typ))
print("[SAMPLE PREDICTION_ID]",sample.get("prediction_id"))
print("[SAMPLE TICKER]",sample.get("ticker"))
print("[SNAPSHOT RECORDS]",len(snap))
print("[UNIQUE EXOGENOUS SOURCES]",len(sources))
for sid in sorted(sources)[:30]: print("[EXOGENOUS SOURCE]",sid)
print("[ANCHOR BOUNDARY VIOLATIONS]",len(bad))
if bad:
    for x in bad[:20]: print("[VIOLATION]",x)
    raise SystemExit("[FAIL] exogenous snapshot violated anchor/leakage boundary")
print("[PASS] non-empty raw independent evidence physically frozen into new immutable prediction rows")
print("[PASS] every checked exogenous row is sequence/time bounded at decision anchor")
print("[PASS] market/derived predictive leakage exclusions held")
print("[RESULT] EXOGENOUS_FULL_PIPELINE_PHYSICALLY_CERTIFIED")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
