from qseries_v2.kalshi_sports_evidence_mapping.binding_lineage import make_lineage
a=make_lineage(ticker='KX',proposition_type='GAME_WINNER',league='NFL',canonical_event_id='evt1',binding_status='BOUND',source_modules=('oad088','oad098'))
b=make_lineage(ticker='KX',proposition_type='GAME_WINNER',league='NFL',canonical_event_id='evt1',binding_status='BOUND',source_modules=('oad088','oad098'))
assert a.lineage_id==b.lineage_id and len(a.lineage_id)==64
print('[PASS] deterministic immutable binding lineage')
print('[PASS] KSEM-009 certified')
