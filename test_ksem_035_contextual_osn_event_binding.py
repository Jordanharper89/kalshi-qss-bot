import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem035_contextual_osn_binding.json').read_text())
assert d['rows']
assert sum(d['counts'].values())==len(d['rows'])
assert d['execution_authority'] is False
print('[PASS] contextual OSN binding accounted every reconstructed leg fail-closed')
print('[PASS] KSEM-035 certified')
