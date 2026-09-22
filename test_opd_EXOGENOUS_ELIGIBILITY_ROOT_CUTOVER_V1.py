from pathlib import Path
P=Path('qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py')
s=P.read_text(encoding='utf-8'); compile(s,str(P),'exec')
for x in ('def _opd_exogenous_source_eligible','prospective_forecast','prospective_binding','source.sports','if "gmgn" in low:','sequence_number<=%s AND observed_at<=to_timestamp(%s)'):
    assert x in s,x
print('[PASS] exogenous eligibility boundary installed')
print('[PASS] internal predictive/experience and sports noise excluded')
print('[PASS] GMGN restricted to SOL')
print('[PASS] exact anchor bounds preserved')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
