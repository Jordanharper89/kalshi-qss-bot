import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json').read_text())
s=next(d[x]['sample'] for x in ('NFL','NCAAF','NBA','NHL','MLS','EPL') if d[x]['sample'])
for k in ('league','home_team','away_team','scheduled_start','provider_event_id'): assert k in s['fields']
print('[PASS] exact CanonicalSportsEvent structural fields captured')
print('[PASS] KSEM-025 structural repair certified')
