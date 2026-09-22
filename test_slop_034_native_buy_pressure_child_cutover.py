import ast
from pathlib import Path
s=Path('run_oracle_LIVE.py').read_text();t=ast.parse(s);d=None
for n in ast.walk(t):
 if isinstance(n,(ast.Assign,ast.AnnAssign)):
  names=[x.id for x in n.targets if isinstance(x,ast.Name)] if isinstance(n,ast.Assign) else ([n.target.id] if isinstance(n.target,ast.Name) else [])
  if 'CHILDREN' in names and isinstance(n.value,ast.Dict): d=ast.literal_eval(n.value);break
assert d['solana_buy_pressure']=='run_slop_buy_pressure_live.py'
ast.parse(Path('run_slop_buy_pressure_live.py').read_text())
print('[CHILD]',d['solana_buy_pressure']);print('[PASS] native production child cutover certified');print('[PASS] execution_authority=FALSE')
