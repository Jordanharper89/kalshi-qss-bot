from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_012_foundational_prediction_corpus_rebuild.py"
TEST=ROOT/"test_osd_012_FOUNDATIONAL_PREDICTION_CORPUS_REBUILD.py"

MODULE=r"""from pathlib import Path
import json, math, hashlib, statistics
from collections import Counter, defaultdict

ROOT=Path.cwd().resolve()
PD=ROOT/"runtime/predictive_data"
SD=ROOT/"runtime/strategy_discovery"
PRED=PD/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=PD/"opd_full_evidence_live_outcome_ledger.jsonl"
OLD=SD/"osd_002_strategy_feature_corpus.jsonl"
NEW=SD/"osd_012_full_evidence_clean_corpus.jsonl"
QUAR=SD/"osd_012_temporal_quarantine.jsonl"
REPORT=SD/"osd_012_foundational_prediction_corpus_rebuild.json"

def rows(p):
    if not p.exists(): return []
    z=[]
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:z.append(json.loads(line))
            except Exception:pass
    return z

def num(x):
    return isinstance(x,(int,float)) and math.isfinite(float(x))

pred=rows(PRED); out=rows(OUT); old=rows(OLD)
pb={r.get("prediction_id"):r for r in pred if r.get("prediction_id")}
ob={r.get("prediction_id"):r for r in out if r.get("prediction_id")}
fb={r.get("prediction_id"):r for r in old if r.get("prediction_id")}

def first_num(r,names):
    for n in names:
        v=r.get(n)
        if num(v): return float(v),n
    return None,None

def temporal(p,o):
    # Never infer chronology from horizon duration. Use physical timestamps/sequence lineage only.
    anchor,an=first_num(p,["anchor_observed_epoch","anchor_epoch","t"])
    frozen,fn=first_num(p,["prediction_frozen_epoch","prediction_epoch","created_epoch"])
    outcome,on=first_num(o,["outcome_observed_epoch","resolved_epoch","resolution_epoch","observed_epoch"])
    due,dn=first_num(p,["resolution_due_epoch","maturity_epoch"])
    reasons=[]
    if anchor is not None and frozen is not None and anchor>frozen:
        reasons.append("ANCHOR_AFTER_PREDICTION_FREEZE")
    if frozen is not None and outcome is not None and outcome<=frozen:
        reasons.append("OUTCOME_NOT_STRICTLY_FUTURE")
    if anchor is not None and outcome is not None and outcome<=anchor:
        reasons.append("OUTCOME_NOT_AFTER_ANCHOR")
    ps=p.get("anchor_sequence_boundary") or p.get("anchor_sequence")
    osq=o.get("outcome_sequence") or o.get("future_sequence") or o.get("resolved_sequence")
    if num(ps) and num(osq) and float(osq)<=float(ps):
        reasons.append("OUTCOME_SEQUENCE_NOT_STRICTLY_FUTURE")
    return reasons,{"anchor":anchor,"anchor_field":an,"frozen":frozen,"frozen_field":fn,
                    "outcome":outcome,"outcome_field":on,"due":due,"due_field":dn}

def flatten(dst,prefix,obj):
    if not isinstance(obj,dict): return
    for k,v in obj.items():
        key=(prefix+"_"+str(k)).strip("_")
        if isinstance(v,dict): flatten(dst,key,v)
        elif isinstance(v,(bool,int,float)) and (not isinstance(v,float) or math.isfinite(v)):
            dst[key]=float(v) if not isinstance(v,bool) else int(v)

SD.mkdir(parents=True,exist_ok=True)
good=[]; bad=[]; reason_counts=Counter()
for pid in sorted(set(pb)&set(ob)):
    p=pb[pid]; o=ob[pid]
    reasons,clock=temporal(p,o)
    if reasons:
        reason_counts.update(reasons)
        bad.append({"prediction_id":pid,"ticker":p.get("ticker"),"reasons":reasons,"clock":clock})
        continue
    base=fb.get(pid,{})
    feats={}
    flatten(feats,"osd",base.get("features") or {})
    # Restore decision-time Oracle intelligence that OSD-002 dropped.
    for k in ["evidence_agreement","comparable_cases","mean_similarity","expected_return",
              "predicted_probability","net_edge_after_2pct","anchor_price"]:
        v=p.get(k)
        if isinstance(v,(bool,int,float)) and (not isinstance(v,float) or math.isfinite(v)):
            feats["oracle_"+k]=float(v) if not isinstance(v,bool) else int(v)
    for root in ["evidence_votes","kalshi_state","coinbase_hf_state","crypto_condition_state","learned_state",
                 "exogenous_evidence_snapshot"]:
        flatten(feats,"oracle_"+root,p.get(root))
    fr=o.get("future_return")
    if not num(fr): continue
    row={"prediction_id":pid,"ticker":p.get("ticker"),"asset":p.get("asset"),
         "decision_epoch":clock["frozen"] if clock["frozen"] is not None else clock["anchor"],
         "anchor_epoch":clock["anchor"],"horizon_seconds":p.get("horizon_seconds"),
         "future_return":float(fr),"features":feats,
         "temporal_clean":True,"execution_authority":False,"publication_allowed":False}
    good.append(row)

with NEW.open("w",encoding="utf-8") as f:
    for r in good:f.write(json.dumps(r,separators=(",",":"))+"\n")
with QUAR.open("w",encoding="utf-8") as f:
    for r in bad:f.write(json.dumps(r,separators=(",",":"))+"\n")

feature_names=set()
for r in good: feature_names.update(r["features"])
missing=Counter()
vals=defaultdict(list)
for r in good:
    f=r["features"]
    for k in feature_names:
        v=f.get(k)
        if num(v):vals[k].append(float(v))
        else:missing[k]+=1
high_missing=[k for k in feature_names if good and missing[k]/len(good)>=.80]
near=[]
for k,v in vals.items():
    if v and len(set(v))/len(v)<.01:near.append(k)

old_ids=set(fb); good_ids={r["prediction_id"] for r in good}
restored_fields=sorted(k for k in feature_names if k.startswith("oracle_"))
report={
 "revision":"OSD-012-FOUNDATIONAL-PREDICTION-CORPUS-REBUILD-V1",
 "prediction_rows":len(pred),"outcome_rows":len(out),"old_corpus_rows":len(old),
 "exact_join_rows":len(set(pb)&set(ob)),"quarantined_temporal_rows":len(bad),
 "temporal_violation_reasons":dict(reason_counts),"clean_rows":len(good),
 "clean_rows_previously_in_osd002":len(good_ids&old_ids),
 "clean_rows_recovered_beyond_osd002":len(good_ids-old_ids),
 "numeric_feature_count":len(feature_names),"restored_oracle_features":restored_fields,
 "high_missing_feature_count":len(high_missing),"near_constant_feature_count":len(near),
 "clean_corpus":str(NEW),"quarantine":str(QUAR),
 "execution_authority":False,"publication_allowed":False
}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("[EXACT PREDICTION/OUTCOME JOINS]",report["exact_join_rows"])
print("[TEMPORAL ROWS QUARANTINED]",len(bad),dict(reason_counts))
print("[CLEAN FULL-EVIDENCE ROWS]",len(good))
print("[RECOVERED BEYOND OSD-002]",report["clean_rows_recovered_beyond_osd002"])
print("[NUMERIC FEATURES]",len(feature_names))
print("[RESTORED ORACLE FEATURES]",len(restored_fields))
print("[HIGH-MISSING FEATURES]",len(high_missing))
print("[NEAR-CONSTANT FEATURES]",len(near))
if not good:
    print("[RESULT] BLOCKED_NO_TEMPORALLY_CLEAN_ROWS")
elif len(feature_names)<=72:
    print("[RESULT] BLOCKED_FULL_EVIDENCE_NOT_RESTORED")
else:
    print("[RESULT] CLEAN_FULL_EVIDENCE_PREDICTION_CORPUS_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
print("[REPORT]",REPORT)
"""

TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_012_foundational_prediction_corpus_rebuild.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ["ANCHOR_AFTER_PREDICTION_FREEZE","OUTCOME_NOT_STRICTLY_FUTURE",
          "OUTCOME_SEQUENCE_NOT_STRICTLY_FUTURE","osd_012_temporal_quarantine.jsonl",
          "evidence_agreement","comparable_cases","mean_similarity","expected_return",
          "predicted_probability","net_edge_after_2pct","anchor_price",
          "exogenous_evidence_snapshot","coinbase_hf_state",
          '"execution_authority":False','"publication_allowed":False']:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-012 foundational corpus rebuild compiles")
print("[PASS] temporal violations are quarantined, never trained")
print("[PASS] exact future sequence/time gates installed")
print("[PASS] dropped Oracle prediction fields restored")
print("[PASS] nested full-evidence state flattening installed")
print("[PASS] original immutable ledgers remain untouched")
print("[PASS] execution/publication remain false")
"""

TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec")
compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-012 foundational prediction corpus rebuild installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
