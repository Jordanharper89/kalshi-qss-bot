from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Callable

from qseries_v2.solana_money_runner import MoneyRunner, REVISION as QSB003_REVISION

REVISION = "QSB-004-REAL-SOLANA-MONEY-RUNNER-V1"
STATE_REL = Path("runtime_state/qseries/solana_real_money_runner")
WORKSPACE_REL = STATE_REL / "workspace"
FEED_REL = Path("runtime_state/solana_opportunities/qsb004_live_price_feed.jsonl")

def _atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)

def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _num(v):
    try:
        x = float(v)
        return x if x == x else None
    except Exception:
        return None

def _default_snapshot_provider(max_tokens: int, timeout: float):
    from qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import (
        discover_live_solana_tokens,
    )
    from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import (
        expand_live_solana_token_pools,
    )

    discovery = discover_live_solana_tokens(timeout_seconds=timeout)
    tokens = list((discovery.payload or {}).get("tokens") or [])[: max(1, int(max_tokens))]
    rows = []
    errors = []
    now = time.time()

    for item in tokens:
        token = str(item.get("token_address") or "")
        if not token:
            continue
        try:
            obs = expand_live_solana_token_pools(token_address=token, timeout_seconds=timeout)
            pools = list((obs.payload or {}).get("pools") or [])
        except Exception as e:
            errors.append({"token": token, "error": type(e).__name__})
            continue

        ranked = []
        for p in pools:
            px = _num(p.get("price_usd"))
            liq = _num(p.get("liquidity_usd"))
            vol = _num(p.get("volume_h24"))
            if px is None or px <= 0:
                continue
            if liq is None or liq < float(os.getenv("QSB004_MIN_LIQUIDITY_USD", "25000")):
                continue
            if vol is None or vol < float(os.getenv("QSB004_MIN_VOLUME_H24_USD", "25000")):
                continue
            ranked.append((liq, p))
        ranked.sort(key=lambda x: x[0], reverse=True)

        for _, p in ranked[:2]:
            rows.append({
                "market_address": str(p.get("pair_address") or ""),
                "token_mint": token,
                "family": str(p.get("dex_id") or "UNKNOWN").upper(),
                "last_price": float(p["price_usd"]),
                "observed_unix": now,
                "liquidity_usd": _num(p.get("liquidity_usd")),
                "volume_usd": _num(p.get("volume_h24")),
                "buy_count": _num(p.get("buys_h24")),
                "sell_count": _num(p.get("sells_h24")),
                "price_basis": "DEXSCREENER_PRICE_USD",
                "source": "QSB004_REAL_SOLANA",
            })

    return {"rows": rows, "errors": errors, "discovered_tokens": len(tokens)}

class RealSolanaMoneyRunner:
    def __init__(
        self,
        root: Path,
        snapshot_provider: Callable | None = None,
        max_tokens: int = 12,
        timeout: float = 12.0,
    ):
        self.root = Path(root).resolve()
        self.state = self.root / STATE_REL
        self.workspace = self.root / WORKSPACE_REL
        self.feed = self.workspace / FEED_REL
        self.snapshot_provider = snapshot_provider or _default_snapshot_provider
        self.max_tokens = int(max_tokens)
        self.timeout = float(timeout)
        self.cycle_number = int(_load_json(self.state / "runtime.json", {}).get("cycle_number") or 0)
        os.environ.setdefault("QSB_ROUNDTRIP_FRICTION", "0.03")

    def _append_rows(self, rows):
        self.feed.parent.mkdir(parents=True, exist_ok=True)
        with self.feed.open("a", encoding="utf-8") as f:
            for row in rows:
                if row.get("market_address") and row.get("token_mint") and _num(row.get("last_price")):
                    f.write(json.dumps(row, sort_keys=True) + "\n")

    def _compact_feed(self, max_lines=50000):
        if not self.feed.exists():
            return
        try:
            lines = self.feed.read_text(encoding="utf-8").splitlines()
            if len(lines) > max_lines:
                self.feed.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _publish_money_files(self):
        src = self.workspace / "runtime_state/qseries/solana_money_runner"
        self.state.mkdir(parents=True, exist_ok=True)
        for name in ("status.json", "ledger.json", "positions.json"):
            p = src / name
            if p.exists():
                (self.state / name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    def cycle(self):
        self.cycle_number += 1
        acquired_at = time.time()
        try:
            snap = self.snapshot_provider(self.max_tokens, self.timeout)
            rows = list(snap.get("rows") or [])
            acquisition_error = None
        except Exception as e:
            rows = []
            snap = {"errors": [], "discovered_tokens": 0}
            acquisition_error = f"{type(e).__name__}: {e}"

        self._append_rows(rows)
        self._compact_feed()

        bot = MoneyRunner(self.workspace)
        money = bot.cycle(progress=False)
        self._publish_money_files()

        reason = None
        if acquisition_error:
            reason = "LIVE_ACQUISITION_ERROR"
        elif not rows:
            reason = "NO_REAL_SOLANA_ROWS_THIS_CYCLE"
        elif money["source_rows"] == 0:
            reason = "NO_USABLE_PRICE_HISTORY"
        elif money["ready_setups"] == 0:
            reason = "NO_READY_SETUP"
        elif money["trades_entered_this_cycle"] == 0 and money["open_positions"] == 0:
            reason = "READY_SETUP_NOT_ENTERED"

        report = {
            "revision": REVISION,
            "qsb003_revision": QSB003_REVISION,
            "cycle_number": self.cycle_number,
            "acquired_unix": acquired_at,
            "real_rows_this_cycle": len(rows),
            "discovered_tokens_this_cycle": int(snap.get("discovered_tokens") or 0),
            "acquisition_errors": list(snap.get("errors") or []),
            "acquisition_error": acquisition_error,
            "price_basis": "DEXSCREENER_PRICE_USD",
            "paper_only": True,
            "real_money_moved": False,
            "money": money,
            "why_no_money_action": reason,
        }
        _atomic_json(self.state / "runtime.json", report)
        return report

def print_report(r):
    m = r["money"]
    print("=" * 118)
    print(" QSB-004 REAL SOLANA MONEY RUNNER")
    print("=" * 118)
    print(
        f"[REAL FEED] cycle={r['cycle_number']} rows_now={r['real_rows_this_cycle']} "
        f"tokens_discovered={r['discovered_tokens_this_cycle']} total_rows={m['source_rows']} "
        f"markets={m['markets_watched']} tokens={m['tokens_watched']}"
    )
    print(
        f"[TRADES] setups={m['setups_found']} ready={m['ready_setups']} "
        f"entered={m['trades_entered_this_cycle']} closed={m['trades_closed_this_cycle']} "
        f"open={m['open_positions']}"
    )
    print(
        f"[MONEY $] closed={m['closed_trades']} wins={m['wins']} losses={m['losses']} "
        f"win_rate={m['win_rate']} gross=${m['gross_pnl_usdc']:.4f} "
        f"friction=${m['modeled_friction_usdc']:.4f} NET=${m['net_pnl_usdc']:.4f}"
    )
    print(
        f"[PROFITABILITY_PROVEN] {m['profitability_proven']} "
        f"[PAPER_ONLY] {r['paper_only']} [REAL_MONEY_MOVED] {r['real_money_moved']}"
    )
    if r["why_no_money_action"]:
        print("[WHY NO MONEY ACTION]", r["why_no_money_action"])
    if r["acquisition_error"]:
        print("[ACQUISITION ERROR]", r["acquisition_error"])
    if r["acquisition_errors"]:
        print("[TOKEN ERRORS]", len(r["acquisition_errors"]))
    if m.get("why_no_trade"):
        print("[WHY NO TRADE]", json.dumps(m["why_no_trade"], sort_keys=True))
    print("[LEDGER]", "runtime_state/qseries/solana_real_money_runner/ledger.json")
    print("=" * 118)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--sleep", type=float, default=float(os.getenv("QSB004_SLEEP_SECONDS", "5")))
    ap.add_argument("--max-tokens", type=int, default=int(os.getenv("QSB004_MAX_TOKENS", "12")))
    ap.add_argument("--timeout", type=float, default=float(os.getenv("QSB004_HTTP_TIMEOUT", "12")))
    args = ap.parse_args()

    runner = RealSolanaMoneyRunner(Path(args.root), max_tokens=args.max_tokens, timeout=args.timeout)
    while True:
        print_report(runner.cycle())
        if args.once:
            break
        time.sleep(max(1.0, args.sleep))

if __name__ == "__main__":
    main()
