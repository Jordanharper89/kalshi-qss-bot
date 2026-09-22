"""Reusable observation session; restart reconstructs the existing OOS from source evidence."""
from pathlib import Path
from .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS, timestamp, utc_now
from .ooi_019_retained_evidence_snapshot import capture_and_retain
from .ooi_021_existing_oos_observation_cycle import observation_cycle, OpportunityOperatingSystem

EXECUTION_AUTHORITY = False

class OpportunityObservationSession:
    def __init__(self, root, oos, policy=None):
        if not isinstance(oos, OpportunityOperatingSystem):
            raise TypeError('Pass the existing caller-owned OpportunityOperatingSystem')
        self.root = Path(root).resolve()
        self.oos = oos
        self.policy = policy
        self.last_capture_at = None
        self.resolution_signature = None
        self.started = False

    def _resolution_signature(self):
        s = (self.root / RESOLUTIONS).stat()
        return s.st_mtime_ns, s.st_size

    def refresh_evidence(self):
        signature_before = self._resolution_signature()
        snapshot = capture_and_retain(self.root)
        self.last_capture_at = snapshot.captured_at
        # A concurrent resolution update triggers another capture on the next step.
        self.resolution_signature = signature_before
        return snapshot

    def start(self, evaluated_at=None):
        self.refresh_evidence()
        report = observation_cycle(self.root, self.oos, evaluated_at=evaluated_at, policy=self.policy)
        self.started = True
        return report

    def step(self, evaluated_at=None):
        if not self.started:
            raise RuntimeError('Call start() before step()')
        now = timestamp(evaluated_at or utc_now())
        age = (now - timestamp(self.last_capture_at)).total_seconds()
        if age < 0:
            raise RuntimeError('Clock moved behind retained evidence capture')
        if age >= 60 or self._resolution_signature() != self.resolution_signature:
            self.refresh_evidence()
        return observation_cycle(self.root, self.oos, evaluated_at=now.isoformat(), policy=self.policy)
