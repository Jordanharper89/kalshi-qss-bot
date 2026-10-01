import ast
import importlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
R=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation')

def main():
    root=Path(__file__).resolve().parent
    source=(root/'run_slop_buy_pressure_live.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    assert sum(isinstance(n.func,ast.Name) and n.func.id=='worker_round' for n in calls)==1
    assert source.index('opportunity_observer.prepare()')<source.index('  x=worker_round(')<source.index('opportunity_observer.complete(x)')
    assert 'token_limit=5' in source and 'time.sleep(5.0)' in source
    assert 'print_prediction(p,' in source and 'resolution_lines(EconomicResolution(**d))' in source
    events=[]
    report={'read_only':True,'execution_authority':False,'accepted':0,'decisions':[]}
    class Session:
        def __init__(self,root,oos): self.started=False;self.oos=oos
        def start(self,at=None): events.append('capture_before_worker');self.started=True;return report
        def step(self,at=None): events.append('observe');return report
    with tempfile.TemporaryDirectory() as tmp, patch.object(R,'OpportunityObservationSession',Session):
        runtime=R.RegisteredChildObservation(tmp)
        runtime.prepare();events.append('worker');status=runtime.complete({'unresolved':0})
        assert events==['capture_before_worker','worker','observe']
        assert runtime.session.oos is runtime.oos and status['round_count']==1
        runtime.failure(RuntimeError('fixture failure'))
        status=json.loads((Path(tmp)/R.STATUS).read_text())
        assert status['state']=='DEGRADED' and status['observation'] is None
        assert status['execution_authority'] is False and status['read_only'] is True
        try: runtime.complete({})
        except RuntimeError: pass
        else: raise AssertionError('Failed preparation admitted a completed round')
    print('[PASS] OOI-026 registered child wiring, pre-worker evidence, same OOS, explicit failure status')
    print('[SCOPE] Deterministic wiring only; restart existing Oracle to load child changes')
    print('[PASS] Frozen worker unchanged; execution_authority=FALSE')

if __name__=='__main__':main()
