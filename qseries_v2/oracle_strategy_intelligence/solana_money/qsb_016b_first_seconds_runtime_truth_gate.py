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
NUM = r"[-+]?\d+(?:\.\d+)?"

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
        m = re.search(rf'(?i)["\']?{re.escape(name)}["\']?\s*[:=]\s*({NUM})', line)
        if m:
            try:
                return cast(float(m.group(1)))
            except (TypeError, ValueError):
                pass
    return None


def analyze_lines(lines: Iterable[str]) -> TruthReport:
    rows = [str(x).rstrip("\r\n") for x in lines]
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
