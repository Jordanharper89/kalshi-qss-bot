from pathlib import Path
ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_002_crypto_learned_experience_depth.py'
BODY=r"""
from collections import Counter,defaultdict
from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from qseries_v2.oracle_adapters.independent.oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics
from qseries_v2.oracle_adapters.independent.oad_192_crypto_comparable_case_sample_sufficiency import assess_comparable_case_sufficiency
from qseries_v2.oracle_adapters.independent.oad_193_crypto_recency_weighted_outcome_statistics import build_recency_weighted_outcome_statistics

cases=read_crypto_learned_case_history(per_asset_limit=512)
by=defaultdict(list)
for x in cases:
    by[x.asset].append(x)
print("[TOTAL_LEARNED_CASES]",len(cases))
for asset in sorted(by):
    rows=by[asset]
    exact=sum(bool(x.exact_interval) for x in rows)
    legacy=sum(bool(x.legacy_timing) for x in rows)
    pos=sum(float(x.return_fraction)>0 for x in rows)
    horizons=Counter(int(x.horizon_seconds) for x in rows)
    newest=max(str(x.outcome_observed_at) for x in rows)
    oldest=min(str(x.outcome_observed_at) for x in rows)
    print("[ASSET]",asset,"cases=",len(rows),"exact=",exact,"legacy=",legacy,
          "positive_share=",round(pos/len(rows),6),"horizons=",dict(horizons),
          "oldest=",oldest,"newest=",newest)

stats=build_comparable_condition_outcome_statistics(cases)
suff=assess_comparable_case_sufficiency(stats)
weighted=build_recency_weighted_outcome_statistics(cases)
ss={(x.asset,x.horizon_seconds,x.condition_signature):x for x in suff}
ww={(x.asset,x.horizon_seconds,x.condition_signature):x for x in weighted}
for x in sorted(stats,key=lambda x:x.sample_size,reverse=True)[:20]:
    s=ss[(x.asset,x.horizon_seconds,x.condition_signature)]
    w=ww[(x.asset,x.horizon_seconds,x.condition_signature)]
    print("[COMPARABLE]",x.asset,x.horizon_seconds,"n=",x.sample_size,
          "raw_positive=",round(x.raw_positive_frequency,6),
          "weighted_positive=",round(w.weighted_positive_share,6),
          "effective_n=",round(w.effective_sample_size,3),"state=",s.sufficiency_state)
assert cases,"no verified crypto learned cases found"
print("[PASS] OPA-002 learned experience depth measured from PostgreSQL")
"""

def main():
    print("="*120)
    print(' ORACLE PREDICTIVE AUDIT 002 CRYPTO LEARNED EXPERIENCE DEPTH INSTALLER')
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",TEST.name)
    print("[PASS] read-only audit; no production mutation")

if __name__=="__main__":
    main()