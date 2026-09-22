from qseries_v2.kalshi_sports_evidence_mapping.entity_league_resolution import resolve_from_existing
assert resolve_from_existing('KX',league='NFL',entities=('Texans','Chiefs')).resolved
assert not resolve_from_existing('KX',league='NFL',entities=('Texans',),ambiguity=('MULTIPLE_MATCHES',)).resolved
print('[PASS] entity/league resolution fail-closes ambiguity')
print('[PASS] KSEM-003 certified')
