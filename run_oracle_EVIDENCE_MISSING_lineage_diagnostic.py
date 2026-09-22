from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LEDGER=ROOT/"runtime_state"/"oracle_learning_event_ledger.json"
LINE="="*80

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def records(obj):
    if isinstance(obj,list): return [x for x in obj if isinstance(x,dict)]
    if isinstance(obj,dict):
        out=[]
        for k,v in obj.items():
            if isinstance(v,dict):
                r=dict(v); r.setdefault("_ledger_key",k); out.append(r)
        return out
    return []

def pick(r,*names):
    for n in names:
        if r.get(n) not in (None,"",[],{}): return r[n]
    return None

def status(r):
    return str(pick(r,"status","learning_status","admission_status","result") or "unknown").lower()

def ticker(r):
    return str(pick(r,"ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol") or "UNKNOWN")

def family(t):
    return t.split("-")[0] if t!="UNKNOWN" else t

def lineage_fields(r):
    needles=("evidence","observation","probability","prediction","reasoning","lineage","sequence","timestamp","settlement","outcome","market")
    return tuple(sorted(k for k,v in r.items() if v not in (None,"",[],{}) and any(n in k.lower() for n in needles)))

def pct(n,d): return 0.0 if not d else 100.0*n/d

def main():
    print(LINE); print(" ORACLE EVIDENCE-MISSING LINEAGE DIAGNOSTIC")
    print(" READ-ONLY — FROZEN OLR-001 THROUGH OLR-045"); print(LINE)
    if not LEDGER.exists():
        print(f"[ERROR] Learning ledger not found: {LEDGER}"); raise SystemExit(2)
    rows=records(load(LEDGER))
    statuses=Counter(status(r) for r in rows)
    missing=[r for r in rows if status(r)=="evidence_missing"]
    learned=[r for r in rows if status(r)=="learned"]
    print(f"[LEDGER] path={LEDGER.relative_to(ROOT)}")
    print(f"[LEDGER] records={len(rows)} statuses={dict(statuses)}")
    print(f"[COMPARE] evidence_missing={len(missing)} learned={len(learned)}"); print("-"*80)

    mf=Counter(family(ticker(r)) for r in missing); lf=Counter(family(ticker(r)) for r in learned)
    print("[EVIDENCE-MISSING] top_market_families=")
    for k,v in mf.most_common(15): print(f"  {k}: {v}")
    print("[LEARNED] top_market_families=")
    for k,v in lf.most_common(15): print(f"  {k}: {v}")
    print("-"*80)

    mk=Counter(); lk=Counter()
    for r in missing: mk.update(lineage_fields(r))
    for r in learned: lk.update(lineage_fields(r))
    diffs=[]
    for k in sorted(set(mk)|set(lk)):
        mp,lp=pct(mk[k],len(missing)),pct(lk[k],len(learned))
        diffs.append((abs(lp-mp),k,mp,lp))
    print("[FIELD COVERAGE] strongest learned-vs-missing differences=")
    for _,k,mp,lp in sorted(diffs,reverse=True)[:20]:
        print(f"  {k}: evidence_missing={mp:.1f}% learned={lp:.1f}% delta={lp-mp:+.1f}pp")
    print("-"*80)

    reasons=Counter(str(pick(r,"reason","failure_reason","ineligibility_reason","evidence_reason","message") or "UNSPECIFIED") for r in missing)
    print(f"[MISSING REASONS] {dict(reasons.most_common(20))}")
    print("[EVIDENCE-MISSING SAMPLE]")
    for r in missing[:10]:
        print(f"  ticker={ticker(r)} fields={lineage_fields(r)} reason={pick(r,'reason','failure_reason','ineligibility_reason','evidence_reason','message')}")
    print("[LEARNED SAMPLE]")
    for r in learned[:10]: print(f"  ticker={ticker(r)} fields={lineage_fields(r)}")
    print("-"*80)

    learned_only=[(k,mp,lp) for _,k,mp,lp in sorted(diffs,reverse=True) if lp>=50.0 and mp<lp]
    overlap=sum(v for k,v in mf.items() if k in lf)
    if learned_only:
        print("[DIAGNOSIS] Learned records consistently carry lineage fields that evidence-missing records lack.")
        print("[LIKELY BOTTLENECK] Recoverable pre-settlement evidence/lineage field coverage.")
        print("[KEY DIFFERENCES]")
        for k,mp,lp in learned_only[:10]: print(f"  {k}: missing={mp:.1f}% learned={lp:.1f}%")
    elif overlap:
        print("[DIAGNOSIS] The same market families appear in both learned and evidence-missing records.")
        print("[LIKELY BOTTLENECK] Per-market evidence timing/lineage availability, not a simple family exclusion.")
    else:
        print("[DIAGNOSIS] Learned and evidence-missing records separate strongly by market family.")
        print("[LIKELY BOTTLENECK] Market-family coverage or identity/evidence routing requires inspection.")
    print("[NEXT] Use these differences to determine whether a defect correction is justified.")
    print("[PASS] Diagnostic performed read-only")
    print("[PASS] Frozen OLR boundary was not modified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE EVIDENCE-MISSING LINEAGE DIAGNOSTIC COMPLETE")

if __name__=="__main__": main()
