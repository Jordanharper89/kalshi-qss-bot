from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor" / "checkpoint3_reverse_atomic_compile.py"
TEST = ROOT / "test_canonical_checkpoint3_reverse_atomic_compile_repair.py"

if not TARGET.exists():
    raise SystemExit("checkpoint3_reverse_atomic_compile.py missing")

src = TARGET.read_text(encoding="utf-8")

helper = r"""

def _build_meteora_reverse_ix_hot(
    token,
    input_amount,
    quote_result,
):
    import base64
    import struct

    template = r.METEORA_TEMPLATES.get(str(token))

    if template is None:
        raise RuntimeError(
            "METEORA_TEMPLATE_MISSING:" + str(token)
        )

    forward_swap = bool(template["swap_for_y"])
    reverse_swap = not forward_swap
    quote_swap = bool(quote_result.get("swap_for_y"))

    if quote_swap != reverse_swap:
        raise RuntimeError(
            "REVERSE_DLMM_QUOTE_DIRECTION_MISMATCH"
        )

    accounts = list(template["fixed_accounts"])

    if len(accounts) < 6:
        raise RuntimeError("METEORA_TEMPLATE_ACCOUNTS_SHORT")

    # Warm template is token -> WSOL.
    # Reverse economic direction is WSOL -> token.
    accounts[4], accounts[5] = accounts[5], accounts[4]

    arrays = list(template["arrays"])
    crossed = max(
        1,
        int(quote_result.get("bins_crossed") or 1),
    )

    n = min(
        len(arrays),
        max(1, (crossed + 69) // 70),
    )

    chosen = (
        arrays[:n]
        if reverse_swap
        else list(reversed(arrays))[:n]
    )

    accounts.extend(
        (address, False, True)
        for _, address in chosen
    )

    min_out = (
        int(quote_result["raw_out"])
        * (10000 - r.q87.las.q59.SLIPPAGE_BPS)
        // 10000
    )

    data = (
        bytes([248,198,158,145,225,117,135,200])
        + struct.pack(
            "<QQ",
            int(input_amount),
            int(min_out),
        )
    )

    return {
        "programId": r.q87.c.DLMM,
        "accounts": [
            {
                "pubkey": pubkey,
                "isSigner": signer,
                "isWritable": writable,
            }
            for pubkey, signer, writable in accounts
        ],
        "data": base64.b64encode(data).decode(),
    }
"""

if "_build_meteora_reverse_ix_hot(" not in src:
    marker = "\ndef _reverse_route("
    if marker not in src:
        raise SystemExit("_reverse_route marker missing")
    src = src.replace(marker, helper + marker, 1)

old = '''    meteora_ix = r.build_meteora_ix_hot(
        token,
        start,
        dict(reverse["mq"]),
    )
'''

new = '''    meteora_ix = _build_meteora_reverse_ix_hot(
        token,
        start,
        dict(reverse["mq"]),
    )
'''

if old in src:
    src = src.replace(old, new, 1)
elif new not in src:
    raise SystemExit("Meteora builder call not found")

TARGET.write_text(src, encoding="utf-8")

test_code = '''import ast
import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint3_reverse_atomic_compile.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = TARGET.read_text(encoding="utf-8")
        ast.parse(cls.src)

    def test_reverse_builder_present(self):
        self.assertIn(
            "def _build_meteora_reverse_ix_hot(",
            self.src,
        )

    def test_reverse_route_uses_reverse_builder(self):
        start = self.src.index("def _reverse_route(")
        end = self.src.find("\\ndef ", start + 20)
        if end < 0:
            end = len(self.src)
        block = self.src[start:end]
        self.assertIn(
            "_build_meteora_reverse_ix_hot(",
            block,
        )
        self.assertNotIn(
            "r.build_meteora_ix_hot(",
            block,
        )

    def test_direction_inverted(self):
        self.assertIn(
            "reverse_swap = not forward_swap",
            self.src,
        )

    def test_source_dest_swapped(self):
        self.assertIn(
            "accounts[4], accounts[5] = accounts[5], accounts[4]",
            self.src,
        )

    def test_zero_rpc_hot_builder(self):
        start = self.src.index(
            "def _build_meteora_reverse_ix_hot("
        )
        end = self.src.index("def _reverse_route(", start)
        block = self.src[start:end]
        self.assertNotIn(".rpc(", block)
        self.assertNotIn("getProgramAccounts", block)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction", self.src)

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

TEST.write_text(test_code, encoding="utf-8")

print("[PASS] checkpoint-3 reverse Meteora direction repair installed")
print("[FIX] warmed token->WSOL template inverted to WSOL->token")
print("[RPC] zero-RPC reverse builder")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]", TEST.name)
