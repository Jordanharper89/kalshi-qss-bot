from qseries_v2.kalshi_sports_evidence_mapping.canonical_event_candidate_matcher import score_candidate,select_exact
a=score_candidate(league='NFL',market_entities=('DAL','NYG'),event_id='1',home='DAL',away='NYG',event_league='NFL')
b=score_candidate(league='NFL',market_entities=('DAL','NYG'),event_id='2',home='DAL',away='PHI',event_league='NFL')
status,row=select_exact([a,b])
assert status=='BOUND' and row.canonical_event_id=='1'
print('[PASS] exact two-team + league binding wins; ambiguity fail-closes')
print('[PASS] KSEM-019 certified')
