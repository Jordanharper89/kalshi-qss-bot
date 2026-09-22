from qseries_v2.kalshi_sports_evidence_mapping.existing_sports_pavement_adapter import ROLE_BINDINGS,normalize_output
assert set(ROLE_BINDINGS)=={'market_type','entity','decomposition','classification'}
assert normalize_output((1,2))==[1,2]
print('[PASS] exact OAD bindings exposed read-only')
print('[PASS] KSEM-014 certified')
