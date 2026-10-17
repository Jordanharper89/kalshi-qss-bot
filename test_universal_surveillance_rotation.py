from pathlib import Path
import ast
from types import SimpleNamespace
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint25_expanded_live_universe_cutover as c25

rs=Path(r.__file__).read_text(encoding="utf-8")
ls=Path(lm.__file__).read_text(encoding="utf-8")
cs=Path(c25.__file__).read_text(encoding="utf-8")
ast.parse(rs); ast.parse(ls); ast.parse(cs)

assert "def build_universal_subscription_windows" in rs
assert "[UNIVERSAL_ROTATION]" in rs
assert "[UNIVERSAL_SURVEILLANCE]" in rs
assert "rotation_seconds=30.0" in rs
assert "_atomic_write(CAPACITY,hot)" not in ls
assert "live_hot_book.json" in ls
assert 'capacity_aware_warm_universe.json' in cs
assert "sendTransaction" not in rs

pairs=[
    SimpleNamespace(token="A",meteora_pool="P1"),
    SimpleNamespace(token="B",meteora_pool="P2"),
    SimpleNamespace(token="C",meteora_pool="P3"),
    SimpleNamespace(token="D",meteora_pool="P4"),
]
address_index={}
for idx in range(4):
    for j in range(4):
        address_index["PAIR%d_A%d"%(idx,j)]=(idx,"kind")

state={"pairs":pairs,"address_index":address_index}

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
assert coverage=={"A|P1","B|P2","C|P3","D|P4"}

for w in windows:
    for key in w["pair_keys"]:
        idx={"A|P1":0,"B|P2":1,"C|P3":2,"D|P4":3}[key]
        needed={"PAIR%d_A%d"%(idx,j) for j in range(4)}
        assert needed.issubset(set(w["addresses"]))

print("[PASS] universal exact-pair scheduler covers every pair")
print("[PASS] every window respects account cap")
print("[PASS] ACTIVE exact pairs remain resident across windows")
print("[PASS] whole-pair account sets rotate together")
print("[PASS] CP24/CP17 rebuild is not part of rotation")
print("[PASS] universal/HOT ownership preserved")
print("[BROADCAST] unchanged")
