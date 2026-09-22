from pathlib import Path
import shutil

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=R/"test_opd_FULL_EVIDENCE_IMMUTABLE_PREDICTION_LEDGER.py"
B=P.with_suffix(".pre_immutable_prediction_ledger.bak")

if not P.exists():
    raise SystemExit("[FAIL] full-evidence predictor missing")

s=P.read_text(encoding="utf-8")
required=("FRESH CANONICAL CUTOVER","contract_horizon","LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME")
for marker in required:
    if marker not in s:
        raise SystemExit("[FAIL] missing required predictor pavement: "+marker)

if "import hashlib,os" not in s:
    s=s.replace("import json,time\n","import json,time\nimport hashlib,os\n",1)

helper = '''PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
PREDICTION_LEDGER_REVISION="FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1"

def _prediction_id(anchor,horizon_seconds):
    raw="|".join([
      PREDICTION_LEDGER_REVISION,
      str(anchor.get("anchor_id") or ""),
      str(anchor.get("anchor_sequence_boundary") or ""),
      str(anchor.get("ticker") or ""),
      str(int(horizon_seconds)),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _freeze_predictions(root,anchor,scores,frozen_epoch):
    path=Path(root)/"runtime"/"predictive_data"/PREDICTION_LEDGER_NAME
    path.parent.mkdir(parents=True,exist_ok=True)
    known=set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    pid=json.loads(line).get("prediction_id")
                    if pid: known.add(str(pid))
                except Exception:
                    pass
    frozen=duplicates=0
    with path.open("a",encoding="utf-8") as f:
        for z in scores:
            h=int(z["horizon_seconds"])
            pid=_prediction_id(anchor,h)
            if pid in known:
                duplicates+=1
                continue
            st=z["state"]
            row={
              "prediction_id":pid,
              "revision":PREDICTION_LEDGER_REVISION,
              "prediction_frozen_epoch":float(frozen_epoch),
              "anchor_id":anchor.get("anchor_id"),
              "anchor_sequence_boundary":anchor.get("anchor_sequence_boundary"),
              "ticker":st.get("ticker"),
              "asset":z.get("asset"),
              "anchor_observed_epoch":float(st.get("observed_epoch")),
              "anchor_price":st.get("anchor_price"),
              "horizon_seconds":h,
              "resolution_due_epoch":float(st.get("observed_epoch"))+h,
              "contract_close_epoch":z.get("contract_close_epoch"),
              "contract_close_basis":anchor.get("contract_close_basis"),
              "horizon_eligible":bool(z.get("horizon_eligible")),
              "direction":z.get("direction"),
              "predicted_probability":z.get("predicted_probability"),
              "expected_return":z.get("expected_return"),
              "net_edge_after_2pct":z.get("net_edge_after_2pct"),
              "comparable_cases":int(z.get("comparable_cases") or 0),
              "unique_tickers":int(z.get("unique_tickers") or 0),
              "mean_similarity":z.get("mean_similarity"),
              "evidence_agreement":z.get("evidence_agreement"),
              "evidence_votes":z.get("evidence_votes"),
              "checks":dict(z.get("checks") or {}),
              "actionable_at_freeze":bool(z.get("passed")),
              "decision_at_freeze":z.get("direction") if z.get("passed") else "ABSTAIN",
              "evidence_tokens":list(st.get("tokens") or []),
              "profitability_status":"PROSPECTIVE_UNRESOLVED",
              "certified":False,
              "publication_allowed":False,
              "execution_authority":False,
            }
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\\n")
            f.flush();os.fsync(f.fileno())
            known.add(pid);frozen+=1
    return {"path":str(path),"frozen":frozen,"duplicates":duplicates}
'''

if "PREDICTION_LEDGER_REVISION=" not in s:
    insert_at=s.index("\ndef run(root=None,now=None,anchor=None):")
    s=s[:insert_at]+"\n"+helper+s[insert_at:]

needle = "    scores=[_score_state(x,history,outcomes,now) for x in current]\n"
replacement = '''    scores=[_score_state(x,history,outcomes,now) for x in current]
    ledger=_freeze_predictions(root,anchor,scores,now)
    print("[PREDICTION LEDGER] frozen=",ledger["frozen"],"duplicates=",ledger["duplicates"],"path=",ledger["path"])
'''
if "[PREDICTION LEDGER]" not in s:
    if needle not in s:
        raise SystemExit("[FAIL] predictor score anchor not found")
    s=s.replace(needle,replacement,1)

if not B.exists():
    shutil.copy2(P,B)
P.write_text(s,encoding="utf-8")

TEST = '''from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.PREDICTION_LEDGER_REVISION=="FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1"

anchor={"anchor_id":"A1","anchor_sequence_boundary":123,"ticker":"KXBTC15M-TEST",
        "contract_close_basis":"LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME"}

def score(h,passed):
    return {
      "state":{"ticker":"KXBTC15M-TEST","observed_epoch":1000.0,"anchor_price":0.55,
               "tokens":["K:A","CB:B","CC:C","L:D"]},
      "asset":"BTC","horizon_seconds":h,"contract_close_epoch":2000.0,
      "horizon_eligible":True,"direction":"DOWN","predicted_probability":0.71,
      "expected_return":0.04,"net_edge_after_2pct":0.02,
      "comparable_cases":40,"unique_tickers":5,"mean_similarity":0.4,
      "evidence_agreement":1.0,"evidence_votes":{"CB":{"direction":"DOWN"}},
      "checks":{"fresh_state":True,"contract_horizon":True,"net_edge":passed},
      "passed":passed
    }

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    first=m._freeze_predictions(root,anchor,[score(60,False),score(300,True)],1100.0)
    second=m._freeze_predictions(root,anchor,[score(60,False),score(300,True)],1130.0)
    p=Path(first["path"])
    rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert first["frozen"]==2 and first["duplicates"]==0
    assert second["frozen"]==0 and second["duplicates"]==2
    assert len(rows)==2
    assert len({r["prediction_id"] for r in rows})==2
    assert {r["horizon_seconds"] for r in rows}=={60,300}
    assert any(r["actionable_at_freeze"] is False and r["decision_at_freeze"]=="ABSTAIN" for r in rows)
    assert any(r["actionable_at_freeze"] is True and r["decision_at_freeze"]=="DOWN" for r in rows)
    assert all(r["profitability_status"]=="PROSPECTIVE_UNRESOLVED" for r in rows)
    assert all(r["execution_authority"] is False and r["publication_allowed"] is False for r in rows)

print("[PASS] immutable prospective prediction ledger append verified")
print("[PASS] deterministic prediction_id prevents duplicate re-freeze of same anchor+horizon")
print("[PASS] actionable AND abstained forecasts are frozen for unbiased prospective scoring")
print("[PASS] resolution_due_epoch and exact anchor lineage persisted")
print("[PASS] fsync append-only persistence enabled")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
T.write_text(TEST,encoding="utf-8")

compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] immutable full-evidence prospective prediction ledger installed")
print("[LEDGER] runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl")
print("[PASS] all live horizons frozen; actionability preserved as a field, not a sampling filter")
print("[PASS] exact anchor/ticker/horizon/evidence/decision lineage persisted")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
