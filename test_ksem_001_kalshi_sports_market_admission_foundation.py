from qseries_v2.kalshi_sports_evidence_mapping.sports_market_admission import admit_from_classification
assert admit_from_classification('KX',is_sports=True,sport='football',league='NFL').admitted
assert not admit_from_classification('KX',is_sports=False).admitted
assert not admit_from_classification('KX',is_sports=True).admitted
print('[PASS] sports admission is explicit and fail-closed')
print('[PASS] KSEM-001 certified')
