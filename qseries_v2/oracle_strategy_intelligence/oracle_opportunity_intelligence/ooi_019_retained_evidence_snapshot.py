"""Retain immutable derived evidence snapshots; existing SLOP ledgers stay untouched."""
from dataclasses import asdict
from pathlib import Path
import json
import os
import tempfile
from .ooi_015_verified_slop_evidence_snapshot import EvidenceSnapshot, read_evidence_snapshot, canonical

EXECUTION_AUTHORITY = False
ARCHIVE = 'runtime_state/oracle_opportunity_intelligence/evidence_snapshots'

def retain_snapshot(snapshot, root=None):
    snapshot.rows()
    root = Path(root or Path.cwd()).resolve()
    directory = root / ARCHIVE
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (snapshot.snapshot_hash + '.json')
    payload = canonical(asdict(snapshot)).encode('utf-8')
    if target.exists():
        if target.read_bytes() != payload:
            raise ValueError('Immutable snapshot path collision/corruption')
        return target
    fd, name = tempfile.mkstemp(prefix='.snapshot-', suffix='.tmp', dir=str(directory))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        # Concurrent writers of the same content-addressed snapshot have identical bytes.
        if target.exists() and target.read_bytes() != payload:
            raise ValueError('Snapshot changed during publication')
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return target

def load_snapshot(path):
    path = Path(path)
    snapshot = EvidenceSnapshot(**json.loads(path.read_text(encoding='utf-8')))
    snapshot.rows()
    if path.name != snapshot.snapshot_hash + '.json':
        raise ValueError('Snapshot filename/hash mismatch')
    return snapshot

def capture_and_retain(root=None):
    snapshot = read_evidence_snapshot(root)
    retain_snapshot(snapshot, root)
    return snapshot
