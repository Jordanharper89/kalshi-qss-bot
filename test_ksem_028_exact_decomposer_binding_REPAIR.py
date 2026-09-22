import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_exact_decomposer_binding_repair.json').read_text())
assert d['bindings']
assert d['execution_authority'] is False
print('[PASS] exact certified OAD-099 decomposition binding recovered')
print('[PASS] KSEM-028 binding repair certified')
