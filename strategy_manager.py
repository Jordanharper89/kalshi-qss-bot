import time
from copy import deepcopy

from position_manager import get_all_positions, save_positions, get_position


DEFAULT_STRATEGY = {
    "enabled": True,
    "name": "Custom",
    "take_profits": [
        {"level": 1, "trigger_pct": 20.0, "sell_pct": 25.0, "fired": False},
        {"level": 2, "trigger_pct": 40.0, "sell_pct": 50.0, "fired": False},
        {"level": 3, "trigger_pct": 75.0, "sell_pct": 25.0, "fired": False},
    ],
    "buy_dips": [
        {"level": 1, "trigger_pct": -10.0, "buy_amount": 10.0, "fired": False},
        {"level": 2, "trigger_pct": -20.0, "buy_amount": 20.0, "fired": False},
    ],
    "stops": [
        {"level": 1, "trigger_pct": -15.0, "sell_pct": 50.0, "fired": False},
        {"level": 2, "trigger_pct": -25.0, "sell_pct": 100.0, "fired": False},
    ],
    "created_at": None,
    "updated_at": None,
}

PRESETS = {
    "SCALP": {
        "enabled": True,
        "name": "Scalp",
        "take_profits": [
            {"level": 1, "trigger_pct": 10.0, "sell_pct": 50.0, "fired": False},
            {"level": 2, "trigger_pct": 20.0, "sell_pct": 50.0, "fired": False},
            {"level": 3, "trigger_pct": 0.0, "sell_pct": 0.0, "fired": False},
        ],
        "buy_dips": [
            {"level": 1, "trigger_pct": -8.0, "buy_amount": 10.0, "fired": False},
            {"level": 2, "trigger_pct": 0.0, "buy_amount": 0.0, "fired": False},
        ],
        "stops": [
            {"level": 1, "trigger_pct": -10.0, "sell_pct": 100.0, "fired": False},
            {"level": 2, "trigger_pct": 0.0, "sell_pct": 0.0, "fired": False},
        ],
    },
    "RUNNER": {
        "enabled": True,
        "name": "Runner",
        "take_profits": [
            {"level": 1, "trigger_pct": 20.0, "sell_pct": 25.0, "fired": False},
            {"level": 2, "trigger_pct": 40.0, "sell_pct": 50.0, "fired": False},
            {"level": 3, "trigger_pct": 75.0, "sell_pct": 25.0, "fired": False},
        ],
        "buy_dips": [
            {"level": 1, "trigger_pct": -10.0, "buy_amount": 10.0, "fired": False},
            {"level": 2, "trigger_pct": -20.0, "buy_amount": 20.0, "fired": False},
        ],
        "stops": [
            {"level": 1, "trigger_pct": -15.0, "sell_pct": 50.0, "fired": False},
            {"level": 2, "trigger_pct": -25.0, "sell_pct": 100.0, "fired": False},
        ],
    },
    "CONSERVATIVE": {
        "enabled": True,
        "name": "Conservative",
        "take_profits": [
            {"level": 1, "trigger_pct": 10.0, "sell_pct": 33.0, "fired": False},
            {"level": 2, "trigger_pct": 20.0, "sell_pct": 33.0, "fired": False},
            {"level": 3, "trigger_pct": 35.0, "sell_pct": 34.0, "fired": False},
        ],
        "buy_dips": [
            {"level": 1, "trigger_pct": -10.0, "buy_amount": 5.0, "fired": False},
            {"level": 2, "trigger_pct": 0.0, "buy_amount": 0.0, "fired": False},
        ],
        "stops": [
            {"level": 1, "trigger_pct": -10.0, "sell_pct": 50.0, "fired": False},
            {"level": 2, "trigger_pct": -18.0, "sell_pct": 100.0, "fired": False},
        ],
    },
}


def _now():
    return int(time.time())


def _ticker(ticker):
    return str(ticker or "").strip().upper()


def _float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.replace("$", "").replace("%", "").strip()
            if not value:
                return default
        return float(value)
    except Exception:
        return default


def normalize_strategy(strategy=None):
    base = deepcopy(DEFAULT_STRATEGY)
    incoming = strategy if isinstance(strategy, dict) else {}

    for key in ["enabled", "name"]:
        if key in incoming:
            base[key] = incoming[key]

    for group in ["take_profits", "buy_dips", "stops"]:
        if isinstance(incoming.get(group), list):
            by_level = {int(x.get("level", i + 1)): x for i, x in enumerate(incoming[group]) if isinstance(x, dict)}
            normalized = []
            for item in base[group]:
                level = int(item.get("level", len(normalized) + 1))
                merged = dict(item)
                if level in by_level:
                    merged.update(by_level[level])
                merged["level"] = level
                merged["fired"] = bool(merged.get("fired", False))
                if "trigger_pct" in merged:
                    merged["trigger_pct"] = _float(merged.get("trigger_pct"), 0.0)
                if "sell_pct" in merged:
                    merged["sell_pct"] = _float(merged.get("sell_pct"), 0.0)
                if "buy_amount" in merged:
                    merged["buy_amount"] = _float(merged.get("buy_amount"), 0.0)
                normalized.append(merged)
            base[group] = normalized

    base["created_at"] = incoming.get("created_at") or _now()
    base["updated_at"] = _now()
    return base


def get_strategy(ticker):
    pos = get_position(_ticker(ticker))
    if not isinstance(pos, dict):
        return normalize_strategy()
    return normalize_strategy(pos.get("strategy"))


def save_strategy(ticker, strategy):
    ticker = _ticker(ticker)
    positions = get_all_positions()
    pos = positions.get(ticker)
    if not isinstance(pos, dict):
        return None
    pos["strategy"] = normalize_strategy(strategy)
    pos["advanced_strategy"] = True
    pos["updated_at"] = _now()
    positions[ticker] = pos
    save_positions(positions)
    return pos["strategy"]


def apply_strategy_preset(ticker, preset_name):
    preset_name = str(preset_name or "RUNNER").upper()
    strategy = deepcopy(PRESETS.get(preset_name, PRESETS["RUNNER"]))
    strategy["created_at"] = _now()
    strategy["updated_at"] = _now()
    return save_strategy(ticker, strategy)


def reset_strategy(ticker):
    return save_strategy(ticker, DEFAULT_STRATEGY)


def update_tp(ticker, level, trigger_pct, sell_pct):
    strategy = get_strategy(ticker)
    level = int(level)
    for item in strategy["take_profits"]:
        if int(item.get("level")) == level:
            item["trigger_pct"] = abs(_float(trigger_pct, 0.0))
            item["sell_pct"] = max(0.0, min(100.0, _float(sell_pct, 0.0)))
            item["fired"] = False
    return save_strategy(ticker, strategy)


def update_buy_dip(ticker, level, trigger_pct, buy_amount):
    strategy = get_strategy(ticker)
    level = int(level)
    trigger = -abs(_float(trigger_pct, 0.0))
    for item in strategy["buy_dips"]:
        if int(item.get("level")) == level:
            item["trigger_pct"] = trigger
            item["buy_amount"] = max(0.0, _float(buy_amount, 0.0))
            item["fired"] = False
    return save_strategy(ticker, strategy)


def update_stop(ticker, level, trigger_pct, sell_pct):
    strategy = get_strategy(ticker)
    level = int(level)
    trigger = -abs(_float(trigger_pct, 0.0))
    for item in strategy["stops"]:
        if int(item.get("level")) == level:
            item["trigger_pct"] = trigger
            item["sell_pct"] = max(0.0, min(100.0, _float(sell_pct, 0.0)))
            item["fired"] = False
    return save_strategy(ticker, strategy)


def reset_fired_flags(ticker):
    strategy = get_strategy(ticker)
    for group in ["take_profits", "buy_dips", "stops"]:
        for item in strategy.get(group, []):
            item["fired"] = False
    return save_strategy(ticker, strategy)


def format_strategy(strategy):
    s = normalize_strategy(strategy)
    lines = [f"Strategy: {s.get('name', 'Custom')}", f"Enabled: {'ON' if s.get('enabled') else 'OFF'}", ""]

    lines.append("TAKE PROFITS")
    for item in s.get("take_profits", []):
        if _float(item.get("trigger_pct"), 0) <= 0 or _float(item.get("sell_pct"), 0) <= 0:
            continue
        fired = "FIRED" if item.get("fired") else "ARMED"
        lines.append(f"TP{item.get('level')}: +{item.get('trigger_pct')}% → Sell {item.get('sell_pct')}% [{fired}]")

    lines.append("")
    lines.append("BUY DIPS")
    for item in s.get("buy_dips", []):
        if _float(item.get("trigger_pct"), 0) >= 0 or _float(item.get("buy_amount"), 0) <= 0:
            continue
        fired = "FIRED" if item.get("fired") else "ARMED"
        lines.append(f"DIP{item.get('level')}: {item.get('trigger_pct')}% → Buy ${item.get('buy_amount')} [{fired}]")

    lines.append("")
    lines.append("STOPS")
    for item in s.get("stops", []):
        if _float(item.get("trigger_pct"), 0) >= 0 or _float(item.get("sell_pct"), 0) <= 0:
            continue
        fired = "FIRED" if item.get("fired") else "ARMED"
        lines.append(f"STOP{item.get('level')}: {item.get('trigger_pct')}% → Sell {item.get('sell_pct')}% [{fired}]")

    return "\n".join(lines).strip()
