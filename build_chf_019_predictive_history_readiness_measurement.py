from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/'qseries_v2'/'oracle_coinbase_high_frequency'
assert (PKG/'chf_016_fixed_grid_historical_window_archive.py').exists()
BODY=r'''
import json
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path

def measure(root=None):
    root=Path(root or Path.cwd()).resolve(); p=root/'runtime'/'coinbase_hf'/'historical_condition_windows.jsonl'
    rows=[]
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            try:rows.append(json.loads(line))
            except:pass
    counts=Counter((r.get('product_id'),int(r.get('window_seconds',0))) for r in rows)
    spans={}
    by=defaultdict(list)
    for r in rows:by[r.get('product_id')].append(float(r.get('anchor_epoch',0)))
    for k,v in by.items():spans[k]=round((max(v)-min(v))/60,3) if len(v)>1 else 0.0
    minimum=min(counts.values()) if counts else 0
    # Measurement only. No arbitrary predictive PASS threshold is imposed here.
    return {'rows':len(rows),'counts':dict(sorted((str(k),v) for k,v in counts.items())),'history_minutes':spans,'minimum_cell_samples':minimum,'predictive_model_ready':False,'reason':'MEASUREMENT_ONLY_REQUIRES_OOS_VALIDATION','probability_enabled':False,'direction_enabled':False,'publication_allowed':False,'execution_authority':False}
'''
TEST=r'''
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_019_predictive_history_readiness_measurement import measure
r=measure(Path.cwd());print('[HISTORY_READINESS]',r)
assert r['predictive_model_ready'] is False
assert r['probability_enabled'] is False and r['execution_authority'] is False
print('[PASS] physical history depth measured without inventing a predictive threshold')
print('[PASS] CHF-019 predictive-history readiness measurement certified')
'''
mod=PKG/'chf_019_predictive_history_readiness_measurement.py';tst=ROOT/'test_chf_019_predictive_history_readiness_measurement.py'
mod.write_text(BODY.lstrip(),encoding='utf-8');tst.write_text(TEST.lstrip(),encoding='utf-8')
for p in (mod,tst):py_compile.compile(str(p),doraise=True)
print('[PASS] wrote CHF-019 history readiness measurement + test')
