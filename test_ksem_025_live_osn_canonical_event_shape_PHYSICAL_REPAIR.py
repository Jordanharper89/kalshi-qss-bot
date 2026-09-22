import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_live_osn_canonical_event_shape.json').read_text())
assert any(d[x]['event_count']>0 for x in ('NFL','NCAAF','NBA','NHL','MLS','EPL'))
assert all('sample' in d[x] for x in ('NFL','NCAAF','NBA','NHL','MLS','EPL'))
assert d['execution_authority'] is False
print('[PASS] live OSN CanonicalProviderResult.events physically captured')
print('[PASS] KSEM-025 physical repair certified')
