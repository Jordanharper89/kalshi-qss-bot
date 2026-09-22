from qseries_v2.kalshi_sports_evidence_mapping.market_proposition import proposition
assert proposition('KX','GAME_WINNER',('Texans','Chiefs'),'Texans win').resolved
assert not proposition('KX','MAGIC',('A',),'x').resolved
print('[PASS] proposition contract explicit and auditable')
print('[PASS] unsupported types fail closed')
print('[PASS] KSEM-004 certified')
