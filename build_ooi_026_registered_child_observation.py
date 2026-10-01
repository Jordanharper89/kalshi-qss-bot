"""Install into the existing Oracle subsystem; stop on physical failure."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
FILES={'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_026_registered_child_observation.py': '"""Observation inside the registered producer; one existing OOS, no acquisition loop."""\nfrom pathlib import Path\nimport json\nimport os\nfrom .ooi_015_verified_slop_evidence_snapshot import utc_now\nfrom .ooi_021_existing_oos_observation_cycle import OpportunityOperatingSystem\nfrom .ooi_022_restart_safe_observation_session import OpportunityObservationSession\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSTATUS = \'runtime_state/oracle_opportunity_intelligence/registered_child_status.json\'\nREVISION = \'OOI_026\'\n\nclass RegisteredChildObservation:\n    def __init__(self, root):\n        self.root = Path(root).resolve()\n        self.oos = OpportunityOperatingSystem()\n        self.session = OpportunityObservationSession(self.root, self.oos)\n        self.round_count = 0\n        self.last_report = None\n        self.prepared = False\n\n    def publish(self, state, worker=None, error=None):\n        payload = dict(revision=REVISION, child=\'run_slop_buy_pressure_live.py\',\n            pid=os.getpid(), updated_at=utc_now(), state=state, round_count=self.round_count,\n            observation=self.last_report, worker=worker, error=error,\n            read_only=True, execution_authority=False,\n            calibrated_probability_available=False, continuous_runtime_activation_certified=False)\n        path = self.root / STATUS\n        path.parent.mkdir(parents=True, exist_ok=True)\n        temp = path.with_name(path.name + \'.%d.tmp\' % os.getpid())\n        try:\n            temp.write_text(json.dumps(payload, sort_keys=True, allow_nan=False), encoding=\'utf-8\')\n            os.replace(temp, path)\n        finally:\n            if temp.exists():\n                temp.unlink()\n        return payload\n\n    def prepare(self, evaluated_at=None):\n        # Capture evidence before the frozen worker can produce this round\'s candidates.\n        self.last_report = None\n        self.prepared = False\n        report = (self.session.step(evaluated_at) if self.session.started\n                  else self.session.start(evaluated_at))\n        self.last_report = report\n        self.prepared = True\n        return self.publish(\'PRODUCER_ROUND_STARTING\')\n\n    def complete(self, worker, evaluated_at=None):\n        if not self.prepared:\n            raise RuntimeError(\'No successful observation before this producer round\')\n        self.last_report = None\n        report = self.session.step(evaluated_at)\n        self.last_report = report\n        self.round_count += 1\n        self.prepared = False\n        return self.publish(\'PRODUCER_AND_OBSERVER_HEALTHY\', worker=worker)\n\n    def failure(self, error):\n        self.last_report = None\n        self.prepared = False\n        return self.publish(\'DEGRADED\', error=repr(error))\n', 'run_slop_buy_pressure_live.py': 'from pathlib import Path\nimport time\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import REVISION as ADMISSION_REVISION\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_025_live_freeze_maturity_resolution_worker import worker_round\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output import print_prediction\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import EconomicResolution\nfrom qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolution_lines\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation import RegisteredChildObservation\nROOT=Path.cwd();seen=set();resolved_seen=set()\nopportunity_observer=RegisteredChildObservation(ROOT)\nprint("[SLOP LIVE] BUY_PRESSURE child STARTING admission_revision=%s execution_authority=FALSE"%ADMISSION_REVISION,flush=True)\nwhile True:\n try:\n  before={p.prediction_id for p in read_predictions(ROOT)}\n  observation_prepared=False\n  try:\n   opportunity_observer.prepare();observation_prepared=True\n  except Exception as observation_error:\n   opportunity_observer.failure(observation_error)\n   print("[OOI LIVE] state=DEGRADED error=%r execution_authority=FALSE"%observation_error,flush=True)\n  x=worker_round(root=ROOT,token_limit=5,progress=lambda z:print(z,flush=True))\n  if observation_prepared:\n   try:\n    opportunity_status=opportunity_observer.complete(x)\n    opportunity_report=opportunity_status["observation"]\n    print("[OOI LIVE] fresh=%s accepted=%s held=%s active=%s execution_authority=FALSE"%tuple(opportunity_report[k] for k in ("fresh_candidates","accepted","held","active_owned_count")),flush=True)\n   except Exception as observation_error:\n    opportunity_observer.failure(observation_error)\n    print("[OOI LIVE] state=DEGRADED error=%r execution_authority=FALSE"%observation_error,flush=True)\n  for p in read_predictions(ROOT):\n   if p.prediction_id not in before and p.prediction_id not in seen:print_prediction(p,progress=lambda z:print(z,flush=True));seen.add(p.prediction_id)\n  for d in read_resolution_dicts(ROOT):\n   if d["prediction_id"] not in resolved_seen:\n    for line in resolution_lines(EconomicResolution(**d)):print(line,flush=True)\n    resolved_seen.add(d["prediction_id"])\n  print("[SLOP LIVE] state=HEALTHY pending=%s execution_authority=FALSE"%x.get("unresolved","?"),flush=True)\n except Exception as e:\n  opportunity_observer.failure(e)\n  print("[SLOP LIVE] state=DEGRADED error=%r execution_authority=FALSE"%e,flush=True)\n time.sleep(5.0)\n', 'test_ooi_026_registered_child_observation.py': "import ast\nimport importlib\nimport json\nfrom pathlib import Path\nimport tempfile\nfrom unittest.mock import patch\nR=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation')\n\ndef main():\n    root=Path(__file__).resolve().parent\n    source=(root/'run_slop_buy_pressure_live.py').read_text(encoding='utf-8')\n    tree=ast.parse(source)\n    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]\n    assert sum(isinstance(n.func,ast.Name) and n.func.id=='worker_round' for n in calls)==1\n    assert source.index('opportunity_observer.prepare()')<source.index('  x=worker_round(')<source.index('opportunity_observer.complete(x)')\n    assert 'token_limit=5' in source and 'time.sleep(5.0)' in source\n    assert 'print_prediction(p,' in source and 'resolution_lines(EconomicResolution(**d))' in source\n    events=[]\n    report={'read_only':True,'execution_authority':False,'accepted':0,'decisions':[]}\n    class Session:\n        def __init__(self,root,oos): self.started=False;self.oos=oos\n        def start(self,at=None): events.append('capture_before_worker');self.started=True;return report\n        def step(self,at=None): events.append('observe');return report\n    with tempfile.TemporaryDirectory() as tmp, patch.object(R,'OpportunityObservationSession',Session):\n        runtime=R.RegisteredChildObservation(tmp)\n        runtime.prepare();events.append('worker');status=runtime.complete({'unresolved':0})\n        assert events==['capture_before_worker','worker','observe']\n        assert runtime.session.oos is runtime.oos and status['round_count']==1\n        runtime.failure(RuntimeError('fixture failure'))\n        status=json.loads((Path(tmp)/R.STATUS).read_text())\n        assert status['state']=='DEGRADED' and status['observation'] is None\n        assert status['execution_authority'] is False and status['read_only'] is True\n        try: runtime.complete({})\n        except RuntimeError: pass\n        else: raise AssertionError('Failed preparation admitted a completed round')\n    print('[PASS] OOI-026 registered child wiring, pre-worker evidence, same OOS, explicit failure status')\n    print('[SCOPE] Deterministic wiring only; restart existing Oracle to load child changes')\n    print('[PASS] Frozen worker unchanged; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"}
PINS={'run_slop_buy_pressure_live.py': '64bdd880605171ed521fbd7e832b07776b0c53c4c6664accc8be477d6fdc3648', 'run_oracle_live.py': 'e9133c5e6641b5b1a11cc7b45037de9a9c677224232802f636730fa12c0c476c'}
TEST='test_ooi_026_registered_child_observation.py'
PREVIOUS='test_ooi_022_restart_safe_observation_session.py'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def write(path,raw):
    temp=path.with_name(path.name+'.install.tmp')
    require(not temp.exists(),'Existing installation temporary file: '+str(temp))
    try:
        temp.write_bytes(raw);os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def clear_cache(path):
    cache=path.parent/'__pycache__'
    if cache.is_dir():
        for item in cache.glob(path.stem+'.*.pyc'):item.unlink()

def main():
    require((ROOT/PREVIOUS).is_file(),'Preceding certified test missing')
    for relative,expected in PINS.items():
        path=ROOT/relative
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,
                'Certified source differs: '+relative)
    original={}
    for relative,source in FILES.items():
        path=ROOT/relative
        require(path.parent.is_dir(),'Existing subsystem missing: '+str(path.parent))
        compile(source,str(path),'exec')
        original[relative]=path.read_bytes() if path.exists() else None
        require(relative in PINS or original[relative] is None or original[relative]==source.encode('utf-8'),
                'Existing target differs: '+relative)
    require(subprocess.run([sys.executable,'-B',str(ROOT/PREVIOUS)],cwd=str(ROOT)).returncode==0,
            'Preceding physical boundary failed; no files changed')
    changed=[]
    try:
        for relative,source in FILES.items():
            path=ROOT/relative
            require((path.read_bytes() if path.exists() else None)==original[relative],'Concurrent source change')
            write(path,source.encode('utf-8'));clear_cache(path);changed.append(relative)
        require(subprocess.run([sys.executable,'-B',str(ROOT/TEST)],cwd=str(ROOT)).returncode==0,
                'Installed deterministic test failed')
    except BaseException:
        for relative in reversed(changed):
            # Retain new tests as failure evidence; restore production changes.
            if relative==TEST:continue
            path=ROOT/relative
            if path.exists() and path.read_bytes()==FILES[relative].encode('utf-8'):
                if original[relative] is None:path.unlink()
                else:write(path,original[relative])
                clear_cache(path)
        print('[ROLLBACK] prior production sources restored; test retained',flush=True)
        raise
    print('[PASS] OOI-026 installed and physically tested; execution_authority=FALSE',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('[FAIL] OOI-026: '+str(exc),flush=True)
        print('[STOP] Do not run the next installer; return full traceback/output',flush=True)
        raise
