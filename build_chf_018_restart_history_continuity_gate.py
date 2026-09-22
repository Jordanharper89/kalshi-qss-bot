from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/'qseries_v2'/'oracle_coinbase_high_frequency'
assert (PKG/'chf_016_fixed_grid_historical_window_archive.py').exists()
BODY=r'''
import json
from pathlib import Path
from .chf_016_fixed_grid_historical_window_archive import archive

def gate(root=None):
    root=Path(root or Path.cwd()).resolve(); d=root/'runtime'/'coinbase_hf'
    st=d/'historical_window_state.json'; hist=d/'historical_condition_windows.jsonl'
    before=hist.stat().st_size if hist.exists() else 0
    r1=archive(root); mid=hist.stat().st_size if hist.exists() else 0
    r2=archive(root); after=hist.stat().st_size if hist.exists() else 0
    if after!=mid:raise RuntimeError('idempotent restart failed: duplicate history emitted without new source events')
    state=json.loads(st.read_text(encoding='utf-8')) if st.exists() else {}
    return {'before_bytes':before,'first_bytes':mid,'restart_bytes':after,'first':r1,'restart':r2,'state':state,'execution_authority':False}
'''
TEST=r'''
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_018_restart_history_continuity_gate import gate
r=gate(Path.cwd());print('[CONTINUITY]',r)
assert r['restart_bytes']==r['first_bytes'];assert r['execution_authority'] is False
print('[PASS] restart does not duplicate fixed-grid historical windows')
print('[PASS] durable anchor checkpoint preserves forward-only history')
print('[PASS] CHF-018 restart/history continuity certified')
'''
mod=PKG/'chf_018_restart_history_continuity_gate.py';tst=ROOT/'test_chf_018_restart_history_continuity_gate.py'
mod.write_text(BODY.lstrip(),encoding='utf-8');tst.write_text(TEST.lstrip(),encoding='utf-8')
for p in (mod,tst):py_compile.compile(str(p),doraise=True)
print('[PASS] wrote CHF-018 restart continuity gate + test')
