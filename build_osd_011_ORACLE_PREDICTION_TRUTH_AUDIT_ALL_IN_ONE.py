from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / "qseries_v2/oracle_strategy_discovery/osd_011_oracle_prediction_truth_audit.py"
TEST = ROOT / "test_osd_011_ORACLE_PREDICTION_TRUTH_AUDIT.py"

MODULE = r"""from pathlib import Path
import json, math, os, statistics
from collections import Counter, defaultdict

ROOT=Path.cwd().resolve()
RUNTIME=ROOT/"runtime"
PRED=RUNTIME/"predictive_data/opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME=RUNTIME/"predictive_data/opd_full_evidence_live_outcome_ledger.jsonl"
CORPUS=RUNTIME/"strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
REPORT=RUNTIME/"strategy_discovery/osd_011_oracle_prediction_truth_audit.json"
TEXT=RUNTIME/"strategy_discovery/osd_011_oracle_prediction_truth_audit.txt"
HURDLE=.02

def load_jsonl(p, limit=None):
    out=[]
    if not p.exists(): return out
    with p.open(encoding="utf-8") as f:
        for line in f:
            try: out.append(json.loads(line))
            except Exception: continue
            if limit and len(out)>=limit: break
    return out

def finite(v):
    return isinstance(v,(int,float)) and math.isfinite(float(v))

pred=load_jsonl(PRED)
out=load_jsonl(OUTCOME)
corpus=load_jsonl(CORPUS)
out_by={r.get("prediction_id"):r for r in out if r.get("prediction_id")}
pred_by={r.get("prediction_id"):r for r in pred if r.get("prediction_id")}

# 1) Corpus representation / lineage
corpus_ids={r.get("prediction_id") for r in corpus if r.get("prediction_id")}
resolved_ids=set(out_by)
prediction_ids=set(pred_by)
corpus_resolved=len(corpus_ids & resolved_ids)
coverage_prediction=(len(corpus_ids)/len(prediction_ids)) if prediction_ids else 0.0
coverage_resolved=(corpus_resolved/len(resolved_ids)) if resolved_ids else 0.0

# 2) Timestamp / anti-leakage integrity
ts_checked=0; ts_viol=0; freeze_after_due=0; anchor_after_freeze=0
freeze_anchor_lags=[]
for r in pred:
    a=r.get("anchor_observed_epoch")
    f=r.get("prediction_frozen_epoch")
    d=r.get("resolution_due_epoch")
    if finite(a) and finite(f):
        ts_checked+=1
        lag=float(f)-float(a); freeze_anchor_lags.append(lag)
        if lag < 0:
            ts_viol+=1; anchor_after_freeze+=1
    if finite(f) and finite(d) and float(f)>float(d):
        ts_viol+=1; freeze_after_due+=1

# 3) Outcome opportunity under fixed 2%
resolved_returns=[]
hurdle_clear_abs=0
for r in out:
    v=r.get("future_return")
    if finite(v):
        x=float(v); resolved_returns.append(x)
        if abs(x)>HURDLE: hurdle_clear_abs+=1
opportunity_rate=hurdle_clear_abs/len(resolved_returns) if resolved_returns else 0.0

# 4) Corpus feature health
feature_values=defaultdict(list)
feature_missing=Counter()
feature_rows=len(corpus)
feature_names=set()
for r in corpus:
    f=r.get("features") or {}
    if isinstance(f,dict):
        feature_names.update(f.keys())
for r in corpus:
    f=r.get("features") or {}
    for k in feature_names:
        v=f.get(k) if isinstance(f,dict) else None
        if finite(v): feature_values[k].append(float(v))
        else: feature_missing[k]+=1

constant=[]; near_constant=[]; high_missing=[]
for k in sorted(feature_names):
    vals=feature_values[k]
    miss=(feature_missing[k]/feature_rows) if feature_rows else 1.0
    if miss>=.80: high_missing.append({"feature":k,"missing_rate":miss})
    if vals:
        uniq=len(set(vals))
        if uniq<=1: constant.append(k)
        elif uniq/max(1,len(vals))<.01: near_constant.append({"feature":k,"unique":uniq,"n":len(vals)})

# duplicate feature columns by sampled value signature
signatures=defaultdict(list)
sample_n=min(5000,feature_rows)
for k in sorted(feature_names):
    sig=[]
    for r in corpus[:sample_n]:
        f=r.get("features") or {}
        v=f.get(k) if isinstance(f,dict) else None
        sig.append(None if not finite(v) else round(float(v),10))
    signatures[tuple(sig)].append(k)
duplicate_groups=[v for v in signatures.values() if len(v)>1]

# 5) Evidence representation in prediction ledger
token_counts=Counter(); vote_keys=Counter(); evidence_nonempty=0
sourceish=Counter()
for r in pred:
    toks=r.get("evidence_tokens") or []
    if toks:
        evidence_nonempty+=1
        for t in toks:
            if isinstance(t,str):
                token_counts[t]+=1
                lo=t.lower()
                if "coinbase" in lo: sourceish["coinbase"]+=1
                if "mempool" in lo or "bitcoin" in lo: sourceish["bitcoin_network"]+=1
                if "kalshi" in lo: sourceish["kalshi"]+=1
                if "solana" in lo: sourceish["solana"]+=1
                if "gmgn" in lo: sourceish["gmgn"]+=1
    votes=r.get("evidence_votes") or {}
    if isinstance(votes,dict):
        for k in votes: vote_keys[k]+=1

# 6) Corpus vs ledger evidence loss
ledger_feature_fields=["evidence_agreement","comparable_cases","mean_similarity","expected_return",
                       "predicted_probability","net_edge_after_2pct","anchor_price"]
ledger_fields_present={k:sum(1 for r in pred if r.get(k) is not None) for k in ledger_feature_fields}
corpus_flat_names=set()
for r in corpus[:1000]:
    corpus_flat_names.update(r.keys())
lost_ledger_fields=[k for k,n in ledger_fields_present.items() if n>0 and k not in corpus_flat_names and k not in feature_names]

# 7) Exact join / label health
joinable=0; bad_future_lineage=0
for pid in prediction_ids & resolved_ids:
    p=pred_by[pid]; o=out_by[pid]
    joinable+=1
    pa=p.get("anchor_sequence_boundary"); oa=o.get("anchor_sequence_boundary")
    if pa is not None and oa is not None and pa!=oa: bad_future_lineage+=1

# 8) Optional PostgreSQL canonical-source freshness around recent prediction anchors
pg={"available":False,"anchors_checked":0,"sources":{},"error":None}
dsn=(os.getenv("ORACLE_POSTGRES_DSN") or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL"))
if dsn:
    try:
        try:
            import psycopg
            conn=psycopg.connect(dsn)
        except Exception:
            import psycopg2
            conn=psycopg2.connect(dsn)
        pg["available"]=True
        anchors=[r for r in pred[-250:] if finite(r.get("anchor_observed_epoch"))]
        src=defaultdict(list)
        cur=conn.cursor()
        for p in anchors:
            ae=float(p["anchor_observed_epoch"])
            cur.execute("""
                SELECT source_id, EXTRACT(EPOCH FROM observed_at)
                FROM public.oracle_canonical_observations
                WHERE observed_at <= to_timestamp(%s)
                  AND observed_at >= to_timestamp(%s)
                  AND source_id <> 'source.kalshi.market_data'
                ORDER BY observed_at DESC
                LIMIT 200
            """,(ae,ae-300.0))
            pg["anchors_checked"]+=1
            seen=set()
            for sid,oe in cur.fetchall():
                if sid in seen: continue
                seen.add(sid)
                try: src[str(sid)].append(ae-float(oe))
                except Exception: pass
        cur.close(); conn.close()
        for sid,lags in src.items():
            if lags:
                pg["sources"][sid]={
                    "n":len(lags),
                    "median_age_s":statistics.median(lags),
                    "p90_age_s":sorted(lags)[min(len(lags)-1,int(.9*(len(lags)-1)))],
                    "fresh_le_5s_rate":sum(x<=5 for x in lags)/len(lags),
                    "fresh_le_30s_rate":sum(x<=30 for x in lags)/len(lags)
                }
    except Exception as e:
        pg["error"]=repr(e)

# 9) Root-cause scoring
findings=[]
def add(severity,code,text):
    findings.append({"severity":severity,"code":code,"text":text})

if coverage_resolved < .50:
    add("CRITICAL","CORPUS_COVERAGE_LOW",f"Strategy corpus contains only {coverage_resolved:.1%} of resolved prediction IDs.")
elif coverage_resolved < .80:
    add("HIGH","CORPUS_COVERAGE_PARTIAL",f"Strategy corpus contains {coverage_resolved:.1%} of resolved prediction IDs.")

if ts_viol:
    add("CRITICAL","TEMPORAL_LINEAGE_VIOLATION",f"{ts_viol} timestamp ordering violations detected.")

if opportunity_rate < .05:
    add("CRITICAL","TWO_PERCENT_OPPORTUNITY_RARE",f"Only {opportunity_rate:.1%} of exact resolved outcomes move more than 2% in absolute terms.")
elif opportunity_rate < .15:
    add("HIGH","TWO_PERCENT_OPPORTUNITY_SPARSE",f"Only {opportunity_rate:.1%} of exact resolved outcomes move more than 2% in absolute terms.")

if high_missing:
    add("HIGH","FEATURE_MISSINGNESS",f"{len(high_missing)} corpus features are >=80% missing.")
if constant or near_constant:
    add("HIGH","LOW_INFORMATION_FEATURES",f"{len(constant)} constant and {len(near_constant)} near-constant features detected.")
if duplicate_groups:
    add("MEDIUM","DUPLICATE_FEATURES",f"{len(duplicate_groups)} duplicate sampled feature groups detected.")
if lost_ledger_fields:
    add("HIGH","EVIDENCE_COLLAPSE_IN_CORPUS","Prediction ledger fields absent from OSD corpus: "+", ".join(lost_ledger_fields))
if evidence_nonempty and len(feature_names)<100:
    add("MEDIUM","RICH_LEDGER_THIN_CORPUS",f"Prediction ledger carries evidence on {evidence_nonempty} rows, while OSD corpus exposes only {len(feature_names)} nested numeric features.")
if pg["available"] and not pg["sources"]:
    add("HIGH","NO_EXTERNAL_CANONICAL_PRELEAD","No non-Kalshi canonical source was found within 300s before sampled decision anchors.")
if not pg["available"]:
    add("INFO","POSTGRES_FRESHNESS_NOT_VERIFIED","PostgreSQL DSN was not available to this process; local audit completed but live source freshness could not be physically verified.")

severity_rank={"CRITICAL":4,"HIGH":3,"MEDIUM":2,"INFO":1}
findings.sort(key=lambda x:severity_rank[x["severity"]],reverse=True)

verdict="NO_SINGLE_ROOT_CAUSE_PROVEN"
if any(x["severity"]=="CRITICAL" for x in findings):
    verdict="FOUNDATIONAL_PREDICTION_INPUT_OR_OBJECTIVE_PROBLEM_DETECTED"
elif any(x["severity"]=="HIGH" for x in findings):
    verdict="MATERIAL_PREDICTION_DATA_PROBLEM_DETECTED"
elif not findings:
    verdict="PREDICTION_DATA_PATH_APPEARS_STRUCTURALLY_HEALTHY_EDGE_STILL_ABSENT"

doc={
 "revision":"OSD-011-ORACLE-PREDICTION-TRUTH-AUDIT-V1",
 "hurdle":HURDLE,
 "counts":{"predictions":len(pred),"outcomes":len(out),"corpus_rows":len(corpus),
           "prediction_ids":len(prediction_ids),"resolved_ids":len(resolved_ids),
           "corpus_ids":len(corpus_ids),"corpus_resolved_ids":corpus_resolved},
 "coverage":{"corpus_vs_predictions":coverage_prediction,"corpus_vs_resolved":coverage_resolved},
 "timestamp_integrity":{"checked":ts_checked,"violations":ts_viol,
                        "anchor_after_freeze":anchor_after_freeze,"freeze_after_due":freeze_after_due,
                        "median_freeze_minus_anchor_s":statistics.median(freeze_anchor_lags) if freeze_anchor_lags else None},
 "economic_opportunity":{"resolved_return_n":len(resolved_returns),"abs_move_gt_2pct_n":hurdle_clear_abs,
                         "abs_move_gt_2pct_rate":opportunity_rate,
                         "median_abs_return":statistics.median([abs(x) for x in resolved_returns]) if resolved_returns else None},
 "feature_health":{"feature_count":len(feature_names),"constant":constant,
                   "near_constant":near_constant,"high_missing":high_missing,
                   "duplicate_groups":duplicate_groups[:50]},
 "evidence_representation":{"prediction_rows_with_tokens":evidence_nonempty,
                            "unique_tokens":len(token_counts),"top_tokens":token_counts.most_common(50),
                            "vote_keys":vote_keys.most_common(50),"sourceish_counts":dict(sourceish),
                            "ledger_fields_present":ledger_fields_present,
                            "ledger_fields_absent_from_corpus":lost_ledger_fields},
 "join_integrity":{"joinable_prediction_outcomes":joinable,"anchor_sequence_mismatches":bad_future_lineage},
 "postgres_freshness":pg,
 "findings":findings,
 "verdict":verdict,
 "execution_authority":False,
 "publication_allowed":False
}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(doc,indent=2),encoding="utf-8")

lines=[
"ORACLE PREDICTION TRUTH AUDIT",
"="*80,
f"PREDICTIONS={len(pred)} OUTCOMES={len(out)} CORPUS_ROWS={len(corpus)}",
f"CORPUS_VS_RESOLVED={coverage_resolved:.2%}",
f"TIMESTAMP_VIOLATIONS={ts_viol}",
f"EXACT_OUTCOMES_ABS_MOVE_GT_2PCT={hurdle_clear_abs}/{len(resolved_returns)} ({opportunity_rate:.2%})",
f"FEATURES={len(feature_names)} CONSTANT={len(constant)} NEAR_CONSTANT={len(near_constant)} HIGH_MISSING={len(high_missing)} DUPLICATE_GROUPS={len(duplicate_groups)}",
f"LEDGER_FIELDS_ABSENT_FROM_CORPUS={lost_ledger_fields}",
f"POSTGRES_FRESHNESS_AVAILABLE={pg['available']} SOURCES_CHECKED={len(pg['sources'])}",
"",
"FINDINGS:"
]
for x in findings: lines.append(f"[{x['severity']}] {x['code']}: {x['text']}")
lines += ["",f"[VERDICT] {verdict}","[EXECUTION/PUBLICATION] FALSE/FALSE"]
TEXT.write_text("\n".join(lines)+"\n",encoding="utf-8")

print("\n".join(lines))
print("[JSON REPORT]",REPORT)
print("[TEXT REPORT]",TEXT)
"""

TESTCODE = r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_011_oracle_prediction_truth_audit.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for needle in [
    "CORPUS_COVERAGE_LOW",
    "TEMPORAL_LINEAGE_VIOLATION",
    "TWO_PERCENT_OPPORTUNITY_RARE",
    "FEATURE_MISSINGNESS",
    "DUPLICATE_FEATURES",
    "EVIDENCE_COLLAPSE_IN_CORPUS",
    "POSTGRES_FRESHNESS_NOT_VERIFIED",
    "oracle_canonical_observations",
    "source_id <> 'source.kalshi.market_data'",
    '"execution_authority":False',
    '"publication_allowed":False'
]:
    assert needle in s, needle
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-011 truth audit compiles")
print("[PASS] corpus coverage audit installed")
print("[PASS] timestamp/anti-leakage audit installed")
print("[PASS] 2% opportunity-density audit installed")
print("[PASS] feature missingness/constancy/duplication audit installed")
print("[PASS] evidence-collapse audit installed")
print("[PASS] optional read-only PostgreSQL freshness audit installed")
print("[PASS] no database mutation statements")
print("[PASS] execution/publication remain false")
"""

TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec")
compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-011 all-in-one Oracle prediction truth audit installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[SCOPE] corpus + outcomes + timestamps + evidence + feature health + 2pct opportunity + optional canonical-source freshness")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
