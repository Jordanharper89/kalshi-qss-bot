"""Select only an archived snapshot known no later than candidate freeze."""
from pathlib import Path
from .ooi_019_retained_evidence_snapshot import ARCHIVE, load_snapshot
from .ooi_015_verified_slop_evidence_snapshot import timestamp
from .ooi_016_asof_comparable_statistics import EvidencePolicy

EXECUTION_AUTHORITY = False

def archived_snapshots(root=None):
    directory = Path(root or Path.cwd()).resolve() / ARCHIVE
    snapshots = [load_snapshot(p) for p in sorted(directory.glob('*.json'))]
    return tuple(sorted(snapshots, key=lambda s: (timestamp(s.captured_at), s.snapshot_hash)))

def select_pre_freeze_snapshot(frozen_at, snapshots, policy=None):
    policy = policy or EvidencePolicy()
    policy.validate()
    cutoff = timestamp(frozen_at)
    known = []
    for snapshot in snapshots:
        snapshot.rows()
        if timestamp(snapshot.captured_at) <= cutoff:
            known.append(snapshot)
    if not known:
        return None, 'NO_RETAINED_PRE_FREEZE_SNAPSHOT'
    selected = max(known, key=lambda s: (timestamp(s.captured_at), s.snapshot_hash))
    if (cutoff - timestamp(selected.captured_at)).total_seconds() > policy.max_snapshot_age_seconds:
        return None, 'STALE_PRE_FREEZE_SNAPSHOT'
    return selected, None
