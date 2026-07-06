import json
import os

SETTINGS_FILE = "trade_settings.json"

DEFAULT_SETTINGS = {
    "advanced_strategy": False,

    # BUY SETTINGS
    "default_buy_amount": 10,
    "quick_buy_amounts": [5, 10, 15, 25, 50, 100],

    # DIP BUY SETTINGS
    "dip_buy_enabled": False,
    "dip_buy_trigger_pct": 10,
    "dip_buy_amount": 10,

    # RISK SETTINGS
    "stop_loss_pct": 20,
    "trailing_stop": False,
    "move_stop_to_breakeven": True,

    # SELL SETTINGS
    "tp1_pct": 20,
    "tp1_sell_pct": 25,

    "tp2_pct": 40,
    "tp2_sell_pct": 50,

    "tp3_pct": 75,
    "tp3_sell_pct": 25,

    "manual_sell_buttons": [25, 50, 75, 100],
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)

        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)
        return settings

    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def toggle_advanced_strategy():
    settings = load_settings()
    settings["advanced_strategy"] = not settings.get("advanced_strategy", False)
    save_settings(settings)
    return settings


def set_default_buy_amount(amount):
    settings = load_settings()
    settings["default_buy_amount"] = float(amount)
    save_settings(settings)
    return settings


def set_quick_buy_amount(index, amount):
    settings = load_settings()
    index = int(index)
    amount = float(amount)

    if index < 0 or index >= len(settings["quick_buy_amounts"]):
        raise ValueError("Invalid preset index")

    settings["quick_buy_amounts"][index] = amount
    save_settings(settings)
    return settings


def toggle_dip_buy():
    settings = load_settings()
    settings["dip_buy_enabled"] = not settings.get("dip_buy_enabled", False)
    save_settings(settings)
    return settings


def set_dip_buy_trigger(percent):
    settings = load_settings()
    settings["dip_buy_trigger_pct"] = float(percent)
    save_settings(settings)
    return settings


def set_dip_buy_amount(amount):
    settings = load_settings()
    settings["dip_buy_amount"] = float(amount)
    save_settings(settings)
    return settings


def set_stop_loss(percent):
    settings = load_settings()
    settings["stop_loss_pct"] = float(percent)
    save_settings(settings)
    return settings


def toggle_trailing_stop():
    settings = load_settings()
    settings["trailing_stop"] = not settings.get("trailing_stop", False)
    save_settings(settings)
    return settings


def toggle_breakeven():
    settings = load_settings()
    settings["move_stop_to_breakeven"] = not settings.get(
        "move_stop_to_breakeven",
        True,
    )
    save_settings(settings)
    return settings


def set_take_profit(tp_level, profit_pct, sell_pct):
    settings = load_settings()
    tp_level = int(tp_level)

    if tp_level not in [1, 2, 3]:
        raise ValueError("tp_level must be 1, 2, or 3")

    settings[f"tp{tp_level}_pct"] = float(profit_pct)
    settings[f"tp{tp_level}_sell_pct"] = float(sell_pct)

    save_settings(settings)
    return settings


def money(amount):
    amount = float(amount)
    if amount.is_integer():
        return "$" + str(int(amount))
    return "$" + str(round(amount, 2))


def format_settings():
    s = load_settings()

    advanced = "ON" if s["advanced_strategy"] else "OFF"
    dip = "ON" if s["dip_buy_enabled"] else "OFF"
    trailing = "ON" if s["trailing_stop"] else "OFF"
    breakeven = "ON" if s["move_stop_to_breakeven"] else "OFF"

    buy_presets = " / ".join([money(x) for x in s["quick_buy_amounts"]])
    sell_buttons = " / ".join([str(x) + "%" for x in s["manual_sell_buttons"]])

    return f"""
TRADE SETTINGS
========================================
Advanced Strategy: {advanced}

BUY SETTINGS
----------------------------------------
Default Buy Amount:
- {money(s["default_buy_amount"])}

Quick Buy Presets:
- {buy_presets}

Dip Buy:
- {dip}

Dip Trigger:
- -{s["dip_buy_trigger_pct"]}%

Dip Buy Amount:
- {money(s["dip_buy_amount"])}

SELL SETTINGS
----------------------------------------
Take Profit Settings:
- TP1: +{s["tp1_pct"]}% | Sell {s["tp1_sell_pct"]}%
- TP2: +{s["tp2_pct"]}% | Sell {s["tp2_sell_pct"]}%
- TP3: +{s["tp3_pct"]}% | Sell {s["tp3_sell_pct"]}%

Manual Sell Buttons:
- {sell_buttons}

RISK SETTINGS
----------------------------------------
Stop Loss:
- {s["stop_loss_pct"]}%

Trailing Stop:
- {trailing}

Move Stop To Breakeven:
- {breakeven}
========================================
""".strip()


if __name__ == "__main__":
    print(format_settings())