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
