from pathlib import Path
import ast,json
root=Path.cwd(); src=(root/'run_oracle_LIVE.py').read_text(encoding='utf-8'); tree=ast.parse(src)
children=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHILDREN' for t in n.targets): children=ast.literal_eval(n.value); break
print('[CHILDREN]',children)
assert children['ksem_mapping']=='run_ksem_live_mapping.py'
assert (root/'run_oracle_LIVE.pre_ksem077.py').is_file()
r=json.loads((root/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem077_native_launcher_cutover.json').read_text())
assert r['execution_authority'] is False
print('[PASS] KSEM child inserted into exact native production CHILDREN dict with rollback backup')
print('[PASS] KSEM-077 certified')
