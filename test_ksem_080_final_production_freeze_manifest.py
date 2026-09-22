from pathlib import Path
import json
p=Path.cwd()/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem080_final_freeze_manifest.json'; r=json.loads(p.read_text())
print('[FREEZE]',r)
assert r['status']=='FROZEN' and r['native_child_key']=='ksem_mapping'
assert r['terminal_dependency']=='NONE' and r['execution_authority'] is False and r['probability_enabled'] is False
assert r['latest_total_rows']>0
print('[PASS] KSEM native production activation frozen through KSEM-080')
print('[PASS] future KSEM changes restricted to genuine defect corrections')
