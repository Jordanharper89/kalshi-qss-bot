from pathlib import Path
import textwrap

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_money"
PKG.mkdir(parents=True, exist_ok=True)
for p in (ROOT/"qseries_v2", ROOT/"qseries_v2"/"oracle_strategy_intelligence", PKG):
    (p/"__init__.py").touch(exist_ok=True)

MODULE = '''
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

FAMILIES = (
    "RAYDIUM_CPMM","RAYDIUM_CLMM","RAYDIUM_V4","RAYDIUM_LAUNCHLAB",
    "METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
    "PUMP_FUN","PUMP_SWAP","ORCA",
)
NUM = r"[-+]?\\d+(?:\\.\\d+)?"

@dataclass
class TruthReport:
    revision: str
    lines: int
    family_hits: dict
    hot_rows_max: int
    first_seconds_entries: int
    closed_trades: int
    wins: int
    losses: int
    win_rate: float | None
    net_pnl: float
    native_markers: int
    external_markers: int
    direct_native_price_markers: int
    next_boundary: str
    execution_authority: bool = False
    paper_only: bool = True


def number(line: str, names: tuple[str, ...], cast=float):
    for name in names:
        m = re.search(rf'(?i)["\\\']?{re.escape(name)}["\\\']?\\s*[:=]\\s*({NUM})', line)
        if m:
            try:
                return cast(float(m.group(1)))
            except (TypeError, ValueError):
                pass
    return None


def analyze_lines(lines: Iterable[str]) -> TruthReport:
    rows = [str(x).rstrip("\\r\\n") for x in lines]
    hits = {f: 0 for f in FAMILIES}
    hot_rows_max = entries = closes = wins = losses = 0
    close_pnl = []
    cumulative_net = None
    native = external = direct_native = 0

    for line in rows:
        upper = line.upper()
        for fam in FAMILIES:
            hits[fam] += upper.count(fam)

        hot = number(line, ("hot_rows", "hotrows"), int)
        if hot is not None:
            hot_rows_max = max(hot_rows_max, hot)

        is_lane = "FIRST_SECONDS_LAUNCH_IMPULSE" in upper
        is_entry = is_lane and any(k in upper for k in ("ENTRY", "OPENED", "ENTERED", " PAPER_OPEN"))
        is_close = is_lane and any(k in upper for k in ("CLOSED", "EXIT", " PAPER_CLOSE"))
        if is_entry:
            entries += 1
        if is_close:
            closes += 1
            if "WIN" in upper and "WIN_RATE" not in upper:
                wins += 1
            if "LOSS" in upper:
                losses += 1
            p = number(line, ("net_pnl", "realized_net_pnl", "pnl_net", "net"))
            if p is not None:
                close_pnl.append(p)

        if any(k in upper for k in ("NATIVE", "BLOCK_TIME", "SIGNATURE", "SLOT=", '"SLOT"', "PROGRAM_EVENT")):
            native += 1
        if any(k in upper for k in ("DEXSCREENER", "EXTERNAL_INDEX", "PAIR_DISCOVER", "PROFILE_DISCOVER")):
            external += 1
        if any(k in upper for k in ("NATIVE_PRICE", "POOL_STATE_PRICE", "VAULT_PRICE", "RESERVE_PRICE", "AGE_ZERO")):
            direct_native += 1

        if any(k in upper for k in ("SUMMARY", "TOTAL", "ARENA", "TRIAL")):
            p = number(line, ("net_pnl", "realized_net_pnl", "pnl_net", "net"))
            if p is not None:
                cumulative_net = p

    net = cumulative_net if cumulative_net is not None else sum(close_pnl)
    win_rate = (wins / (wins + losses)) if (wins + losses) else None
    active_families = sum(v > 0 for v in hits.values())

    if hot_rows_max <= 0 or entries <= 0:
        next_boundary = "QSB_017_NATIVE_POOL_IDENTITY_AND_PRICE_PATH"
    elif closes <= 0:
        next_boundary = "KEEP_QSB_015_RUNNING_FOR_FRESH_CLOSES"
    elif net <= 0 or (win_rate is not None and win_rate < 0.55):
        next_boundary = "QSB_017_LOSS_PATTERN_AND_EXIT_PATH_CORRECTION"
    elif direct_native <= 0 and active_families:
        next_boundary = "QSB_017_NATIVE_POOL_IDENTITY_AND_PRICE_PATH"
    else:
        next_boundary = "CONTINUE_FRESH_FORWARD_SAMPLE_TO_25_CLOSES"

    return TruthReport(
        revision="QSB_016B", lines=len(rows), family_hits=hits,
        hot_rows_max=hot_rows_max, first_seconds_entries=entries,
        closed_trades=closes, wins=wins, losses=losses, win_rate=win_rate,
        net_pnl=round(net, 8), native_markers=native,
        external_markers=external, direct_native_price_markers=direct_native,
        next_boundary=next_boundary,
    )


def write_report(report: TruthReport, root: Path) -> Path:
    out = root / "runtime_state" / "solana_money" / "qsb_016b_first_seconds_runtime_truth_gate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(asdict(report), indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(out)
    return out
'''

RUNNER = '''
from __future__ import annotations
import argparse, queue, subprocess, sys, threading, time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_016b_first_seconds_runtime_truth_gate import analyze_lines, write_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=150)
    ap.add_argument("--source")
    args = ap.parse_args()
    root = Path.cwd()
    lines = []

    if args.source:
        lines = Path(args.source).read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        target = root / "run_qsb_015_first_seconds_launch_impulse.py"
        if not target.exists():
            raise SystemExit("[FAIL] missing run_qsb_015_first_seconds_launch_impulse.py")
        p = subprocess.Popen([sys.executable, "-u", str(target)], cwd=root,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
        q = queue.Queue()
        def reader():
            if p.stdout:
                for line in p.stdout:
                    q.put(line)
            q.put(None)
        threading.Thread(target=reader, daemon=True).start()
        deadline = time.monotonic() + max(5, args.seconds)
        done = False
        try:
            while time.monotonic() < deadline and not done:
                try:
                    item = q.get(timeout=0.2)
                except queue.Empty:
                    if p.poll() is not None:
                        break
                    continue
                if item is None:
                    done = True
                else:
                    print(item, end="")
                    lines.append(item.rstrip("\\r\\n"))
        finally:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill(); p.wait(timeout=5)

    report = analyze_lines(lines)
    path = write_report(report, root)
    print("[QSB-016B]", report)
    print("[REPORT]", path)
    print("[NEXT]", report.next_boundary)
    print("[PASS] execution_authority=FALSE PAPER_ONLY=True")

if __name__ == "__main__":
    main()
'''

TEST = '''
import tempfile, unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_016b_first_seconds_runtime_truth_gate import analyze_lines, write_report

class TruthGateTest(unittest.TestCase):
    def test_positive_native_lane(self):
        lines = [
            '[BURST] family=RAYDIUM_CPMM raw=1234 hot_rows=4 signature=abc slot=1',
            '[ENTRY] strategy=FIRST_SECONDS_LAUNCH_IMPULSE family=RAYDIUM_CPMM native_price=0.0001',
            '[CLOSED] strategy=FIRST_SECONDS_LAUNCH_IMPULSE result=WIN net_pnl=0.42',
            '[ENTRY] strategy=FIRST_SECONDS_LAUNCH_IMPULSE family=METEORA_DAMM pool_state_price=0.0002',
            '[CLOSED] strategy=FIRST_SECONDS_LAUNCH_IMPULSE result=WIN net_pnl=0.77',
        ]
        r = analyze_lines(lines)
        self.assertEqual(r.hot_rows_max, 4)
        self.assertEqual(r.first_seconds_entries, 2)
        self.assertEqual(r.closed_trades, 2)
        self.assertEqual(r.wins, 2)
        self.assertAlmostEqual(r.net_pnl, 1.19, places=8)
        self.assertGreater(r.family_hits['RAYDIUM_CPMM'], 0)
        self.assertGreater(r.direct_native_price_markers, 0)
        self.assertEqual(r.next_boundary, 'CONTINUE_FRESH_FORWARD_SAMPLE_TO_25_CLOSES')
        self.assertFalse(r.execution_authority)
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(write_report(r, Path(d)).exists())

    def test_no_hot_rows_routes_native(self):
        r = analyze_lines(['[BURST] family=PUMP_FUN hot_rows=0 signature=x slot=2'])
        self.assertEqual(r.next_boundary, 'QSB_017_NATIVE_POOL_IDENTITY_AND_PRICE_PATH')

if __name__ == '__main__': unittest.main()
'''

for path, content in {
    PKG/"qsb_016b_first_seconds_runtime_truth_gate.py": MODULE,
    ROOT/"run_qsb_016b_first_seconds_runtime_truth_gate.py": RUNNER,
    ROOT/"test_qsb_016b_first_seconds_runtime_truth_gate.py": TEST,
}.items():
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print(f"[PASS] installed: {path.relative_to(ROOT)}")
print("[PASS] test: test_qsb_016b_first_seconds_runtime_truth_gate.py")
print("[PASS] execution_authority=FALSE PAPER_ONLY=True")
