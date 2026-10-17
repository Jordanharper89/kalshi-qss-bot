from pathlib import Path

ROOT = Path.cwd()
RUNTIME = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor" / "runtime.py"
TEST = ROOT / "test_canonical_compile_429_resilience.py"

if not RUNTIME.exists():
    raise SystemExit("runtime.py missing")

src = RUNTIME.read_text(encoding="utf-8")

helper = r"""

def _canonical_compile_candidate_429_resilient(
    user,
    instructions,
    alt_options,
    blockhash,
):
    import time as _time
    import urllib.error as _urllib_error

    last = None

    for attempt in range(6):
        try:
            return q87.compile_candidate(
                user,
                instructions,
                alt_options,
                blockhash,
            )

        except _urllib_error.HTTPError as exc:
            last = exc

            if getattr(exc, "code", None) != 429:
                raise

            delay = min(
                4.0,
                0.50 * (2 ** attempt),
            )

            print(
                "[CANONICAL_ALT_429_RETRY] "
                "attempt=%d sleep=%.2fs"
                % (
                    attempt + 1,
                    delay,
                ),
                flush=True,
            )

            _time.sleep(delay)

    if last is not None:
        raise last

    raise RuntimeError(
        "CANONICAL_COMPILE_RETRY_EXHAUSTED"
    )
"""

if "_canonical_compile_candidate_429_resilient" not in src:
    marker = "\ndef compile_current("
    if marker not in src:
        raise SystemExit("compile_current marker missing")

    src = src.replace(
        marker,
        helper + marker,
        1,
    )

old = "q87.compile_candidate("
new = "_canonical_compile_candidate_429_resilient("

start = src.find("def compile_current(")
if start < 0:
    raise SystemExit("compile_current missing after helper insertion")

end = src.find("\ndef ", start + 20)
if end < 0:
    end = len(src)

block = src[start:end]

if new not in block:
    if old not in block:
        raise SystemExit("compile_current q87.compile_candidate call missing")

    block = block.replace(
        old,
        new,
    )

    src = src[:start] + block + src[end:]

RUNTIME.write_text(src, encoding="utf-8")

test_code = '''import ast
import unittest
from pathlib import Path

RUNTIME = Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)


class T(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = RUNTIME.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.src)

    def test_retry_helper_present(self):
        self.assertIn(
            "def _canonical_compile_candidate_429_resilient(",
            self.src,
        )

    def test_only_429_is_retried(self):
        self.assertIn(
            'getattr(exc, "code", None) != 429',
            self.src,
        )

    def test_bounded_retry(self):
        self.assertIn(
            "for attempt in range(6):",
            self.src,
        )
        self.assertIn(
            "CANONICAL_COMPILE_RETRY_EXHAUSTED",
            self.src,
        )

    def test_compile_current_uses_wrapper(self):
        start = self.src.index(
            "def compile_current("
        )
        end = self.src.find(
            "\ndef ",
            start + 20,
        )
        if end < 0:
            end = len(self.src)

        block = self.src[start:end]

        self.assertIn(
            "_canonical_compile_candidate_429_resilient(",
            block,
        )

    def test_no_execution_change(self):
        h0 = self.src.index(
            "def _canonical_compile_candidate_429_resilient("
        )
        h1 = self.src.index(
            "def compile_current("
        )
        self.assertNotIn(
            "sendTransaction",
            self.src[h0:h1],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

TEST.write_text(test_code, encoding="utf-8")

print("[PASS] canonical compile 429 resilience installed")
print("[SCOPE] solana_atomic_executor/runtime.py only")
print("[RETRY] HTTP 429 only, 6 bounded attempts")
print("[BACKOFF] 0.50s -> capped at 4.00s")
print("[ALT] existing canonical HSEM table unchanged")
print("[KEY] QSB_SOLANA_PRIVATE_KEY untouched")
print("[BROADCAST] unchanged")
print("[TEST]", TEST.name)
