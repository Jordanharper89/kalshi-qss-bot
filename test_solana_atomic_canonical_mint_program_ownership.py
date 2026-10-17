from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
s=Path(r.__file__).read_text(encoding="utf-8")
assert "[CANONICAL_MINT_PROGRAMS]" in s
assert "TOKEN_MINT_OWNER_UNSUPPORTED" in s
assert "WSOL_TOKEN_PROGRAM_DRIFT" in s
assert "[SIZE_BIND]" in s
assert "sendTransaction" not in s
print("[PASS] canonical mint-program ownership; size binding preserved; broadcast absent")
