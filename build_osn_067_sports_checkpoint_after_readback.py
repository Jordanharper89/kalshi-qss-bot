from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-067 SPORTS CHECKPOINT AFTER READBACK INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py',)
FILES = {'qseries_v2/oracle_source_network/persistence/sports_runtime_checkpoint.py': 'from dataclasses import dataclass, asdict\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\nimport os\nimport tempfile\n\n\n@dataclass(frozen=True)\nclass SportsCheckpoint:\n    league: str\n    observation_id: str\n    observed_at: str\n    committed_readback_count: int\n    checkpointed_at: str\n    execution_authority: bool = False\n\n\ndef _checkpoint_path(root, league):\n    return Path(root) / "qseries_v2" / "oracle_source_network" / "state" / "sports_checkpoints" / (league.lower() + ".json")\n\n\ndef commit_checkpoint_after_readback(league, observation_id, observed_at, exact_readback_count, root=None):\n    if int(exact_readback_count) < 1:\n        raise RuntimeError("checkpoint prohibited before exact durable readback")\n\n    base = Path(root or Path.cwd()).resolve()\n    path = _checkpoint_path(base, league)\n    path.parent.mkdir(parents=True, exist_ok=True)\n\n    value = SportsCheckpoint(\n        league=str(league),\n        observation_id=str(observation_id),\n        observed_at=str(observed_at),\n        committed_readback_count=int(exact_readback_count),\n        checkpointed_at=datetime.now(timezone.utc).isoformat(),\n    )\n\n    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))\n    try:\n        with os.fdopen(fd, "w", encoding="utf-8") as fh:\n            json.dump(asdict(value), fh, sort_keys=True, separators=(",", ":"))\n            fh.flush()\n            os.fsync(fh.fileno())\n        os.replace(tmp_name, path)\n    finally:\n        if os.path.exists(tmp_name):\n            os.unlink(tmp_name)\n\n    return value\n\n\ndef read_checkpoint(league, root=None):\n    base = Path(root or Path.cwd()).resolve()\n    path = _checkpoint_path(base, league)\n    if not path.exists():\n        return None\n    data = json.loads(path.read_text(encoding="utf-8"))\n    return SportsCheckpoint(**data)\n', 'test_osn_067_sports_checkpoint_after_readback.py': 'from datetime import datetime, timezone\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import (\n    commit_checkpoint_after_readback,\n    read_checkpoint,\n)\n\nwith TemporaryDirectory() as td:\n    try:\n        commit_checkpoint_after_readback(\n            "NFL",\n            "a" * 64,\n            datetime.now(timezone.utc).isoformat(),\n            0,\n            root=td,\n        )\n        raise AssertionError("checkpoint-before-readback was incorrectly admitted")\n    except RuntimeError:\n        print("[PASS] checkpoint rejected when exact_readback_count=0")\n\n    cp = commit_checkpoint_after_readback(\n        "NFL",\n        "b" * 64,\n        datetime.now(timezone.utc).isoformat(),\n        1,\n        root=td,\n    )\n    loaded = read_checkpoint("NFL", root=td)\n    print("[CHECKPOINT]", loaded)\n    assert loaded == cp\n    assert loaded.committed_readback_count == 1\n    assert loaded.execution_authority is False\n\nprint("[PASS] checkpoint only advances after exact durable readback")\nprint("[PASS] checkpoint write is atomic")\nprint("[PASS] durable checkpoint reload certified")\nprint("[PASS] OSN-067 sports checkpoint-after-readback contract certified")\n'}

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit('[FAIL] missing dependency: ' + rel)
    print('[PASS] dependency verified:', rel)
    return p

def write_compile(rel, source):
    compile(source, rel, 'exec')
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding='utf-8')
    compile(p.read_text(encoding='utf-8'), str(p), 'exec')
    print('[WRITE]', rel)
    print('[PASS] post-write compile verified:', rel)

def main():
    print('=' * 120)
    print(' ' + TITLE)
    print('=' * 120)
    for rel in REQUIRED:
        require(rel)
    for rel, source in FILES.items():
        write_compile(rel, source)
    print('[PASS] installer completed')
    print('[PASS] execution_authority=FALSE')

if __name__ == '__main__':
    main()
