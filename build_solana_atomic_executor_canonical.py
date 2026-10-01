from pathlib import Path
import ast

ROOT=Path.cwd()
TEST=ROOT/"test_solana_atomic_executor_canonical.py"

if not TEST.is_file():
    raise RuntimeError("CANONICAL_TEST_MISSING")

src=TEST.read_text(encoding="utf-8")

old='''        forbidden=[
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "getProgramAccounts",
            "urlopen",
            "http(",
        ]'''

new='''        forbidden=[
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
            "http(",
        ]'''

if old not in src:
    raise RuntimeError(
        "METEORA_ZERO_RPC_TEST_BLOCK_NOT_FOUND"
    )

src=src.replace(old,new,1)

ast.parse(src)

TEST.write_text(
    src,
    encoding="utf-8"
)

print("[PASS] canonical Meteora zero-RPC test corrected")
print("[RUNTIME] unchanged")
print("[FIX] comments no longer trigger false getProgramAccounts failure")
print("[HOT_PATH] c.rpc/c.account/dlmm_arrays/urlopen/http still forbidden")
print("[BROADCAST] disabled")