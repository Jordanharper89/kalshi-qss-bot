from pathlib import Path

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"checkpoint4_message_fee_economics_gate.py"
TEST=ROOT/"test_canonical_checkpoint4_fee_429_resilience.py"

if not TARGET.is_file():
    raise SystemExit("checkpoint4_message_fee_economics_gate.py missing")

src=TARGET.read_text(encoding="utf-8")

old='''    result=r.q87.c.rpc(
        "getFeeForMessage",
        [
            encoded,
            {
                "commitment":"processed",
            },
        ],
    )
'''

new='''    import time
    import urllib.error

    last=None

    for attempt in range(6):
        try:
            result=r.q87.c.rpc(
                "getFeeForMessage",
                [
                    encoded,
                    {
                        "commitment":"processed",
                    },
                ],
            )
            break
        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429:
                raise

            delay=min(
                4.0,
                0.50*(2**attempt),
            )

            print(
                "[CHECKPOINT4_FEE_429_RETRY] "
                "attempt=%d sleep=%.2fs"
                %(
                    attempt+1,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)
    else:
        raise last or RuntimeError(
            "CHECKPOINT4_FEE_RPC_RETRY_EXHAUSTED"
        )
'''

if old in src:
    src=src.replace(old,new,1)
elif "[CHECKPOINT4_FEE_429_RETRY]" not in src:
    raise SystemExit("getFeeForMessage RPC block not found")

TARGET.write_text(src,encoding="utf-8")

test_code='''import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint4_message_fee_economics_gate.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_fee_retry_present(self):
        self.assertIn(
            "[CHECKPOINT4_FEE_429_RETRY]",
            self.s,
        )

    def test_bounded_attempts(self):
        self.assertIn(
            "for attempt in range(6):",
            self.s,
        )

    def test_only_429_retried(self):
        self.assertIn(
            'getattr(exc,"code",None)!=429',
            self.s,
        )

    def test_fee_rpc_preserved(self):
        self.assertIn(
            '"getFeeForMessage"',
            self.s,
        )

    def test_economics_unchanged(self):
        self.assertIn(
            "after=gross-fee",
            self.s,
        )
        self.assertIn(
            "admitted=after>0",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
'''

TEST.write_text(test_code,encoding="utf-8")

print("[PASS] checkpoint-4 fee RPC 429 resilience installed")
print("[SCOPE] getFeeForMessage only")
print("[RETRY] HTTP 429 only, 6 bounded attempts")
print("[ECONOMICS] unchanged")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
