
from pathlib import Path
from collections import deque
import argparse
import json
import shutil
import time
import unittest

VERSION = "ORACLE_031_MRIYA_TO_ATOMIC_CANDIDATE_BRIDGE"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST = PKG / "oracle_031_mriya_candidate_bridge.py"
SOURCE = Path("runtime_state/qseries/qarb_clean_bot/candidates.jsonl")
OUT = Path("runtime_state/oracle/oracle_live_execution/mriya_bridge_candidates.jsonl")
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_031_BRIDGE.json")
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TTL = 30.0

def valid_key(value):
    if not isinstance(value, str):
        return False
    if not 32 <= len(value) <= 44:
        return False
    try:
        n = 0
        for ch in value:
            n = n * 58 + ALPHABET.index(ch)
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
        raw = b"\0" * (len(value) - len(value.lstrip("1"))) + raw
        return len(raw) == 32
    except (ValueError, OverflowError):
        return False

def admission(row, now=None):
    now = time.time() if now is None else now
    if not isinstance(row, dict):
        return None, "NOT_OBJECT"
    if row.get("execution_authority") is not False:
        return None, "AUTHORITY_NOT_READ_ONLY"
    try:
        observed = float(row["observed_unix"])
    except (KeyError, TypeError, ValueError):
        return None, "MISSING_OBSERVATION_TIME"
    age = now - observed
    if age < -2 or age > TTL:
        return None, "STALE_OR_FUTURE_SIGNAL"
    fields = ("token", "pump_pool", "meteora_pool")
    if not all(valid_key(row.get(key)) for key in fields):
        return None, "INCOMPLETE_POOL_IDENTITY"
    if row["pump_pool"] == row["meteora_pool"]:
        return None, "SAME_POOL_IDENTITY"
    if row.get("direction") not in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        return None, "BAD_DIRECTION"
    try:
        size = float(row["size_sol"])
    except (KeyError, TypeError, ValueError):
        return None, "BAD_SIZE"
    if not 0 < size <= 10:
        return None, "BAD_SIZE"
    return {
        "revision": VERSION,
        "source_revision": str(row.get("revision", "")),
        "source": str(row.get("source", "")),
        "token": row["token"],
        "pump_pool": row["pump_pool"],
        "meteora_pool": row["meteora_pool"],
        "observed_unix": observed,
        "signal_age_ms": round(age * 1000, 1),
        "discovery_direction": row["direction"],
        "discovery_size_sol": size,
        "executor_canary_lamports": 10000000,
        "requires_fresh_onchain_validation": True,
        "requires_exact_repricing": True,
        "requires_protected_atomic_simulation": True,
        "execution_authority": False,
        "signing": False,
        "broadcast": False
    }, "STAGED"

def evaluate(rows, now=None):
    now = time.time() if now is None else now
    chosen, reasons = {}, {}
    for row in rows:
        candidate, reason = admission(row, now)
        if candidate is None:
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        token = candidate["token"]
        if token not in chosen or (
            candidate["observed_unix"] > chosen[token]["observed_unix"]
        ):
            chosen[token] = candidate
    return list(chosen.values()), reasons

def recent_rows(path, maximum=256):
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as handle:
        raw = deque(handle, maxlen=maximum)
    rows = []
    for line in raw:
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows

def append_candidates(root, rows):
    path = root / OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

def run(root, watch_seconds):
    source = root / SOURCE
    accepted, rejected = 0, {}
    seen = set()
    start = time.monotonic()
    position = 0
    if watch_seconds:
        position = source.stat().st_size if source.is_file() else 0
    while True:
        rows = []
        if not watch_seconds:
            rows = recent_rows(source)
        elif source.is_file():
            with source.open("r", encoding="utf-8") as handle:
                handle.seek(position)
                for line in handle:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
                position = handle.tell()
        candidates, reasons = evaluate(rows)
        for key, count in reasons.items():
            rejected[key] = rejected.get(key, 0) + count
        fresh = []
        for row in candidates:
            identity = (row["token"], row["observed_unix"])
            if identity not in seen:
                seen.add(identity)
                fresh.append(row)
        if fresh:
            append_candidates(root, fresh)
            accepted += len(fresh)
            print("[BRIDGE_STAGED]", len(fresh), flush=True)
        if not watch_seconds or time.monotonic() - start >= watch_seconds:
            break
        time.sleep(0.25)
    report = {
        "revision": VERSION,
        "status": "HANDOFF_STAGED_NOT_BOUND",
        "source_exists": source.is_file(),
        "staged_candidates": accepted,
        "rejections": rejected,
        "source_path": str(SOURCE),
        "output_path": str(OUT),
        "executor_consumer_connected": False,
        "live_scanner_activated_by_bridge": False,
        "rpc_requests": 0,
        "signing": False,
        "broadcast": False
    }
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    for key, value in report.items():
        print("[" + key.upper() + "]", json.dumps(value))
    return 0

class Tests(unittest.TestCase):
    def sample(self):
        return {
            "execution_authority": False,
            "observed_unix": 100.0,
            "token": "So11111111111111111111111111111111111111112",
            "pump_pool": "11111111111111111111111111111111",
            "meteora_pool": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            "direction": "PUMP_TO_METEORA",
            "size_sol": 0.01
        }
    def test_stage(self):
        row, reason = admission(self.sample(), 101)
        self.assertEqual(reason, "STAGED")
        self.assertFalse(row["execution_authority"])
    def test_stale(self):
        self.assertEqual(admission(self.sample(), 140)[1], "STALE_OR_FUTURE_SIGNAL")
    def test_read_only(self):
        row = self.sample()
        row["execution_authority"] = True
        self.assertIsNone(admission(row, 101)[0])
    def test_dedup(self):
        rows, _ = evaluate([self.sample(), self.sample()], 101)
        self.assertEqual(len(rows), 1)
    def test_missing_identity(self):
        row = self.sample()
        row.pop("pump_pool")
        self.assertEqual(admission(row, 101)[1], "INCOMPLETE_POOL_IDENTITY")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--watch", type=int, default=0)
    args = parser.parse_args()
    root = Path.cwd()
    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1
    if args.audit or args.watch:
        if args.watch and not 1 <= args.watch <= 120:
            print("[HOLD] WATCH_LIMIT_1_TO_120")
            return 2
        return run(root, args.watch)
    dest = root / DEST
    if not dest.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if dest.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), dest)
    print("[PASS]", VERSION)
    print("[MRIYA] ORIGINAL_PRODUCER_UNCHANGED")
    print("[EXECUTION] DISABLED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
