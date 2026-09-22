from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import latest_live_anchor,_opd_load_exogenous_canonical_asof
root=Path.cwd().resolve(); a=latest_live_anchor(root)
if not a: raise SystemExit('[FAIL] no live anchor')
x=_opd_load_exogenous_canonical_asof(a,root)
print('[ANCHOR]',a.get('ticker'),a.get('anchor_sequence_boundary'),a.get('observed_epoch'))
print('[ELIGIBLE EXOGENOUS SOURCES]',len(x))
bad=[]
for v in x.values():
    sid=str(v.get('source_id') or ''); typ=str(v.get('observation_type') or ''); low=(sid+' '+typ).lower()
    print('[ELIGIBLE SOURCE]',v.get('sequence_number'),sid,typ)
    if any(z in low for z in ('prospective_forecast','prospective_binding','experience','source.sports','sports.','kalshi','coinbase','polymarket','learned_case')):
        bad.append((sid,typ))
if bad:
    for z in bad: print('[BAD SOURCE]',z)
    raise SystemExit('[FAIL] contaminated source survived')
if not x: raise SystemExit('[FAIL] no eligible exogenous evidence at anchor')
print('[PASS] only eligible external decision-time evidence survives')
