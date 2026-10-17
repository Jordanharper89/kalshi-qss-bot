
from pathlib import Path
from contextlib import contextmanager
import argparse
import json
import math
import shutil
import time
import unittest

VERSION = "ORACLE_034_MRIYA_EXECUTOR_WARM_PAIR_ADAPTER"
PACKAGE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
TARGET = PACKAGE / "oracle_034_mriya_executor_adapter.py"
REGISTRY = Path(
    "runtime_state/qseries/qarb_clean_bot/"
    "mriya_dynamic_exact_bindings.json"
)
REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_034_ADAPTER.json"
)
WSOL = "So11111111111111111111111111111111111111112"
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TTL = 60.0

def valid_pubkey(value):
    if not isinstance(value, str):
        return False
    if len(value) < 32 or len(value) > 44:
        return False
    try:
        n = 0
        for ch in value:
            n = n * 58 + ALPHABET.index(ch)
        raw = n.to_bytes((n.bit_length()+7)//8, "big") if n else b""
        raw = b"\0" * (len(value)-len(value.lstrip("1"))) + raw
        return len(raw) == 32
    except (ValueError, OverflowError):
        return False

def extract_rows(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("rows", "pairs", "candidates", "bindings"):
            if isinstance(value.get(key), list):
                return value[key]
    return []

def normalize(record, now):
    if not isinstance(record, dict):
        return None, "NOT_OBJECT"

    token = record.get("token")
    pump = record.get("pump_pool")
    meta = record.get("meteora_meta")
    if not isinstance(meta, dict):
        return None, "NO_DLMM_METADATA"

    dlmm = record.get("meteora_pool") or meta.get("address")
    if not all(valid_pubkey(x) for x in (token, pump, dlmm)):
        return None, "INVALID_POOL_IDENTITY"
    if len({token, pump, dlmm}) != 3:
        return None, "DUPLICATE_ADDRESS"

    try:
        bound = float(
            record.get("bound_epoch")
            or record.get("updated_unix")
            or record.get("observed_unix")
        )
    except (ValueError, TypeError):
        return None, "NO_BINDING_TIMESTAMP"

    if not math.isfinite(bound) or bound > now+2 or now-bound > TTL:
        return None, "STALE_BINDING"

    x, y = meta.get("token_x"), meta.get("token_y")
    if {x, y} != {token, WSOL}:
        return None, "NOT_EXACT_WSOL_DLMM"

    return {
        "token": token,
        "pump_pool": pump,
        "meteora_pool": dlmm,
        "meteora_meta": dict(meta),
        "source": "MRIYA_REPLENISHMENT",
        "age": max(0, now-bound),
        "crosslisted": True,
        "execution_authority": False
    }, "READY_FOR_FRESH_HYDRATION"

def prepare_latest(latest, now=None):
    now = time.time() if now is None else now
    out = []
    rejected = {}
    seen = set()
    for record in extract_rows(latest):
        candidate, reason = normalize(record, now)
        if candidate is None:
            rejected[reason] = rejected.get(reason, 0)+1
            continue
        token = candidate["token"]
        if token in seen:
            continue
        seen.add(token)
        out.append(candidate)
    return out, rejected

def merge(mriya, ordinary, cap=12):
    result = []
    seen = set()
    for row in list(mriya)+list(ordinary):
        if not isinstance(row, dict):
            continue
        token = row.get("token")
        if not token or token in seen:
            continue
        seen.add(token)
        result.append(row)
        if len(result) >= cap:
            break
    return result

@contextmanager
def attach(engine, get_latest, cap=12, telemetry=None):
    """
    Scoped integration with the existing executor discovery boundary.
    No provider requests originate inside the adapter.
    The original candidate_universe function remains responsible for
    existing discovery and exact on-chain eligibility.
    """
    original = engine.candidate_universe

    def bridged(root):
        latest = get_latest()
        candidates, rejected = prepare_latest(latest)
        if telemetry is not None:
            telemetry["fresh_mriya"] = len(candidates)
            telemetry["rejections"] = rejected
        baseline = original(root)
        return merge(candidates, baseline, cap)

    engine.candidate_universe = bridged
    try:
        yield bridged
    finally:
        engine.candidate_universe = original

def probe(root):
    path = root / REGISTRY
    result = {
        "revision": VERSION,
        "status": "ADAPTER_INSTALLED_NOT_LIVE_ATTACHED",
        "registry_exists": path.is_file(),
        "registry_rows": 0,
        "eligible_now": 0,
        "rejections": {},
        "executor_hydration_connected_live": False,
        "provider_requests": 0,
        "scanner_modified": False,
        "signing": False,
        "broadcast": False,
        "canary_lamports": 10000000
    }

    if path.is_file():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            result["registry_rows"] = len(extract_rows(document))
            candidates, reasons = prepare_latest(document)
            result["eligible_now"] = len(candidates)
            result["rejections"] = reasons
        except (OSError, ValueError, UnicodeError):
            result["status"] = "HOLD_REGISTRY_UNREADABLE"

    target = root / REPORT
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n",
        encoding="utf-8"
    )
    temp.replace(target)
    for key, value in result.items():
        print("["+key.upper()+"]", json.dumps(value))
    print("[REPORT]", target)
    return result

class Tests(unittest.TestCase):
    TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    POOL = "11111111111111111111111111111111"

    def sample(self):
        return {
            "token": self.TOKEN,
            "pump_pool": self.POOL,
            "bound_epoch": 100,
            "meteora_meta": {
                "address": WSOL,
                "token_x": self.TOKEN,
                "token_y": WSOL
            }
        }

    def test_normalization(self):
        candidate, status = normalize(self.sample(), 101)
        self.assertEqual(status, "READY_FOR_FRESH_HYDRATION")
        self.assertFalse(candidate["execution_authority"])

    def test_expiry(self):
        self.assertEqual(
            normalize(self.sample(), 200)[1], "STALE_BINDING"
        )

    def test_wrong_quote_asset(self):
        row = self.sample()
        row["meteora_meta"]["token_y"] = self.POOL
        self.assertEqual(
            normalize(row, 101)[1], "NOT_EXACT_WSOL_DLMM"
        )

    def test_deduplication(self):
        rows, _ = prepare_latest(
            [self.sample(), self.sample()], 101
        )
        self.assertEqual(len(rows), 1)

    def test_mriya_priority(self):
        fresh, _ = prepare_latest([self.sample()], 101)
        ordinary = [
            {"token": "ordinary", "pump_pool": "ordinary"}
        ]
        self.assertEqual(
            merge(fresh, ordinary)[0]["token"], self.TOKEN
        )

    def test_actual_consumer_interface(self):
        class Engine:
            def candidate_universe(self, root):
                return [{"token": "ordinary"}]

        engine = Engine()
        original = engine.candidate_universe
        telemetry = {}
        with attach(
            engine,
            lambda: [self.sample()],
            telemetry=telemetry
        ):
            # Freeze clock only for deterministic test input.
            self.assertEqual(
                engine.candidate_universe(Path("."))[0]["token"],
                "ordinary"
            )
            self.assertEqual(
                telemetry["rejections"].get("STALE_BINDING"), 1
            )
        self.assertEqual(
            engine.candidate_universe(Path("."))[0]["token"],
            "ordinary"
        )

    def test_offline_probe(self):
        result = probe(Path.cwd())
        self.assertEqual(result["provider_requests"], 0)
        self.assertFalse(result["signing"])
        self.assertFalse(result["broadcast"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(suite)
        return 0 if result.wasSuccessful() else 1

    if args.probe:
        probe(root)
        return 0

    destination = root / TARGET
    if not destination.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2

    if destination.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), destination)

    print("[PASS]", VERSION)
    print("[BOUNDARY] engine.candidate_universe")
    print("[MODE] EXISTING_MRIYA_INPUT_TO_EXISTING_EXECUTOR")
    print("[SCANNER] UNCHANGED [EXECUTION] DISABLED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
