from pathlib import Path
import ast
from types import SimpleNamespace
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm

src=Path(r.__file__).read_text(encoding="utf-8")
lms=Path(lm.__file__).read_text(encoding="utf-8")
ast.parse(src)
ast.parse(lms)

assert "UNIVERSAL_STATE_BINDING" in src
assert "CANONICAL_ADDRESS_MAP_NOT_FOUND" in src
assert 'state.get("address_index")' not in src
assert "_atomic_write(CAPACITY,hot)" not in lms
assert "live_hot_book.json" in lms
assert "sendTransaction" not in src

pairs=[
    SimpleNamespace(token="A",meteora_pool="P1"),
    SimpleNamespace(token="B",meteora_pool="P2"),
    SimpleNamespace(token="C",meteora_pool="P3"),
    SimpleNamespace(token="D",meteora_pool="P4"),
]

addresses=[]
canonical_lookup={}

for idx in range(4):
    for j in range(4):
        a="PAIR%d_A%d"%(idx,j)
        addresses.append(a)
        canonical_lookup[a]=(idx,"kind_%d"%j)

state={
    "pairs":pairs,
    "addresses":addresses,
    "native_event_lookup":canonical_lookup,
    "unrelated_dict":{"x":"y"},
}

windows=r.build_universal_subscription_windows(
    state,
    max_accounts=8,
    hot_keys=["A|P1","B|P2"],
    active_keys=["A|P1"],
)

assert len(windows)>=2
assert all(len(w["addresses"])<=8 for w in windows)
assert all("A|P1" in w["pair_keys"] for w in windows)

coverage={
    key
    for w in windows
    for key in w["pair_keys"]
}

assert coverage=={
    "A|P1","B|P2","C|P3","D|P4"
}

for w in windows:
    for key in w["pair_keys"]:
        idx={
            "A|P1":0,
            "B|P2":1,
            "C|P3":2,
            "D|P4":3,
        }[key]
        needed={
            "PAIR%d_A%d"%(idx,j)
            for j in range(4)
        }
        assert needed.issubset(
            set(w["addresses"])
        )

print("[PASS] canonical hydrated address map auto-discovered")
print("[PASS] scheduler no longer assumes state['address_index']")
print("[PASS] every exact pair retains its full watched-account set")
print("[PASS] all exact pairs covered across bounded windows")
print("[PASS] ACTIVE exact pair remains resident")
print("[PASS] universal/HOT ownership preserved")
print("[BROADCAST] unchanged")
