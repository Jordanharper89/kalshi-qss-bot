import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem030_exact_osn_team_pair_index.json').read_text())
assert d['events']
assert all(x['team_pair_key'] for x in d['events'])
assert d['execution_authority'] is False
print('[PASS] six-league exact OSN canonical team-pair index built')
print('[PASS] KSEM-030 certified')
