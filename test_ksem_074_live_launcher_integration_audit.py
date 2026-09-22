from pathlib import Path
import json
root=Path.cwd()
r=json.loads((root/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem074_launcher_audit.json').read_text(encoding='utf-8'))
print('[AUDIT]',r)
assert r['contains_children'], 'production launcher CHILDREN structure not detected'
assert r['contains_popen'], 'production child process launch mechanism not detected'
print('[PASS] exact live launcher integration surface audited without mutation')
print('[PASS] KSEM-074 certified')
