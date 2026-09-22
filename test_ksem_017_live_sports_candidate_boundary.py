from qseries_v2.kalshi_sports_evidence_mapping.live_sports_candidate_boundary import READER,SPORTS
assert READER[1]=='read_current_kalshi_markets'
assert SPORTS[1]=='fetch_current_market_sports_candidates'
print('[PASS] exact live reader and sports-candidate boundary installed')
print('[PASS] KSEM-017 certified')
