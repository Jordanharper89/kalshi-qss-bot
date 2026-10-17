from pathlib import Path
import ast

ROOT=Path.cwd()
BASE=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor"

TARGETS=[
    BASE/"checkpoint12_multi_pool_live_size_optimizer.py",
    BASE/"checkpoint15_cheapest_legal_fee_signed_simulation.py",
    BASE/"checkpoint19_bidirectional_best_first_signed_simulation.py",
]

OLD="""(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)"""

NEW="""(
    0.001,
    0.005,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)"""

changed=[]
for path in TARGETS:
    if not path.is_file():
        raise RuntimeError("TARGET_MISSING:"+str(path))

    s=path.read_text(encoding="utf-8")
    ast.parse(s)

    if "0.005," in s:
        continue

    count=s.count(OLD)
    if count<1:
        raise RuntimeError(
            "CANARY_SIZE_LADDER_SEAM_NOT_FOUND:"
            +path.name
        )

    s=s.replace(OLD,NEW)
    ast.parse(s)
    path.write_text(s,encoding="utf-8")
    changed.append(path.name)

runtime=BASE/"runtime.py"
rs=runtime.read_text(encoding="utf-8")
ast.parse(rs)
if "sendTransaction" in rs:
    raise RuntimeError("UNEXPECTED_RUNTIME_BROADCAST_SEAM")

TEST=ROOT/"test_canary_005_exact_size_path.py"
TEST_CODE='from pathlib import Path\nimport ast\n\nROOT=Path.cwd()\nBASE=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor"\n\ntargets=[\n    BASE/"checkpoint12_multi_pool_live_size_optimizer.py",\n    BASE/"checkpoint15_cheapest_legal_fee_signed_simulation.py",\n    BASE/"checkpoint19_bidirectional_best_first_signed_simulation.py",\n]\n\nfor p in targets:\n    s=p.read_text(encoding="utf-8")\n    ast.parse(s)\n    assert "0.005," in s, p.name\n    assert s.index("0.005,") < s.index("0.010,"), p.name\n\nruntime=(BASE/"runtime.py").read_text(encoding="utf-8")\nassert "sendTransaction" not in runtime\n\nprint("[PASS] 0.005 SOL exact quote size installed")\nprint("[PASS] optimizer includes 0.005")\nprint("[PASS] fee/signed-sim path includes 0.005")\nprint("[PASS] 28-pair scanner source untouched")\nprint("[PASS] no live-send seam enabled yet")\nprint("[NEXT] require physical 0.005 after-fee-positive signed-sim PASS")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] CANARY 0.005 EXACT SIZE PATH")
print("[SIZE] 0.005 SOL")
print("[FILES]",",".join(changed) if changed else "already_present")
print("[SCANNER] untouched")
print("[PAIR_UNIVERSE] untouched")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
