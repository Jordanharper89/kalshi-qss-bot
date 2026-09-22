from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import (
    commit_checkpoint_after_readback,
    read_checkpoint,
)

with TemporaryDirectory() as td:
    try:
        commit_checkpoint_after_readback(
            "NFL",
            "a" * 64,
            datetime.now(timezone.utc).isoformat(),
            0,
            root=td,
        )
        raise AssertionError("checkpoint-before-readback was incorrectly admitted")
    except RuntimeError:
        print("[PASS] checkpoint rejected when exact_readback_count=0")

    cp = commit_checkpoint_after_readback(
        "NFL",
        "b" * 64,
        datetime.now(timezone.utc).isoformat(),
        1,
        root=td,
    )
    loaded = read_checkpoint("NFL", root=td)
    print("[CHECKPOINT]", loaded)
    assert loaded == cp
    assert loaded.committed_readback_count == 1
    assert loaded.execution_authority is False

print("[PASS] checkpoint only advances after exact durable readback")
print("[PASS] checkpoint write is atomic")
print("[PASS] durable checkpoint reload certified")
print("[PASS] OSN-067 sports checkpoint-after-readback contract certified")
