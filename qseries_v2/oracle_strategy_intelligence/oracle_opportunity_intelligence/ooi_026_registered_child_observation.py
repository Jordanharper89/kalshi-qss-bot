"""Observation inside the registered producer; one existing OOS, no acquisition loop."""
from pathlib import Path
import json
import os
from .ooi_015_verified_slop_evidence_snapshot import utc_now
from .ooi_021_existing_oos_observation_cycle import OpportunityOperatingSystem
from .ooi_022_restart_safe_observation_session import OpportunityObservationSession

EXECUTION_AUTHORITY = False
READ_ONLY = True
STATUS = 'runtime_state/oracle_opportunity_intelligence/registered_child_status.json'
REVISION = 'OOI_026'

class RegisteredChildObservation:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.oos = OpportunityOperatingSystem()
        self.session = OpportunityObservationSession(self.root, self.oos)
        self.round_count = 0
        self.last_report = None
        self.prepared = False

    def publish(self, state, worker=None, error=None):
        payload = dict(revision=REVISION, child='run_slop_buy_pressure_live.py',
            pid=os.getpid(), updated_at=utc_now(), state=state, round_count=self.round_count,
            observation=self.last_report, worker=worker, error=error,
            read_only=True, execution_authority=False,
            calibrated_probability_available=False, continuous_runtime_activation_certified=False)
        path = self.root / STATUS
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + '.%d.tmp' % os.getpid())
        try:
            temp.write_text(json.dumps(payload, sort_keys=True, allow_nan=False), encoding='utf-8')
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()
        return payload

    def prepare(self, evaluated_at=None):
        # Capture evidence before the frozen worker can produce this round's candidates.
        self.last_report = None
        self.prepared = False
        report = (self.session.step(evaluated_at) if self.session.started
                  else self.session.start(evaluated_at))
        self.last_report = report
        self.prepared = True
        return self.publish('PRODUCER_ROUND_STARTING')

    def complete(self, worker, evaluated_at=None):
        if not self.prepared:
            raise RuntimeError('No successful observation before this producer round')
        self.last_report = None
        report = self.session.step(evaluated_at)
        self.last_report = report
        self.round_count += 1
        self.prepared = False
        return self.publish('PRODUCER_AND_OBSERVER_HEALTHY', worker=worker)

    def failure(self, error):
        self.last_report = None
        self.prepared = False
        return self.publish('DEGRADED', error=repr(error))
