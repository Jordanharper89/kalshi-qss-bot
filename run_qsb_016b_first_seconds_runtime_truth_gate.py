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
                    lines.append(item.rstrip("\r\n"))
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
