from qseries_v2.kalshi_sports_evidence_mapping.canonical_event_binding import bind_exact
x=bind_exact('KX','NFL',('Texans','Chiefs'),canonical_event_id='evt1',canonical_home='Chiefs',canonical_away='Texans')
assert x.status=='BOUND'
y=bind_exact('KX','NFL',('Texans',),ambiguity=('MULTIPLE_EVENTS',))
assert y.status=='AMBIGUOUS'
z=bind_exact('KX','NFL',('Texans','Bills'),canonical_event_id='evt1',canonical_home='Chiefs',canonical_away='Texans')
assert z.status=='REJECTED'
print('[PASS] canonical event binding requires exact identity')
print('[PASS] KSEM-008 certified')
