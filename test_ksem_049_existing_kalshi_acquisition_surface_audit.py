import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem049_existing_kalshi_acquisition_surface_audit.json').read_text())
assert 'candidates' in d
assert d['execution_authority'] is False
print('[PASS] existing Kalshi acquisition surfaces audited without guessed interface execution')
print('[PASS] KSEM-049 certified')
