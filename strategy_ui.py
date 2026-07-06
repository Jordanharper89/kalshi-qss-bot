from strategy_manager import get_strategy, format_strategy, PRESETS

TP_TRIGGERS = [10, 20, 30, 40, 50, 75]
SELL_PCTS = [10, 25, 50, 75, 100]
DIP_TRIGGERS = [5, 10, 15, 20, 25, 30]
BUY_AMOUNTS = [5, 10, 20, 40]
STOP_TRIGGERS = [5, 10, 15, 20, 25, 30]


def strategy_text(ticker):
    strategy = get_strategy(ticker)
    return f"""
ADVANCED STRATEGY BUILDER

Ticker:
{ticker}

{format_strategy(strategy)}

Use this screen to control when the bot sells profits, buys dips, and cuts risk.
""".strip()


def strategy_keyboard(ticker):
    rows = [
        [
            {"text": "Apply Scalp", "callback_data": f"strategy_preset|{ticker}|SCALP"},
            {"text": "Apply Runner", "callback_data": f"strategy_preset|{ticker}|RUNNER"},
        ],
        [
            {"text": "Apply Conservative", "callback_data": f"strategy_preset|{ticker}|CONSERVATIVE"},
        ],
        [
            {"text": "Edit TP1", "callback_data": f"strategy_tp_trigger_menu|{ticker}|1"},
            {"text": "Edit TP2", "callback_data": f"strategy_tp_trigger_menu|{ticker}|2"},
            {"text": "Edit TP3", "callback_data": f"strategy_tp_trigger_menu|{ticker}|3"},
        ],
        [
            {"text": "Edit Dip1", "callback_data": f"strategy_dip_trigger_menu|{ticker}|1"},
            {"text": "Edit Dip2", "callback_data": f"strategy_dip_trigger_menu|{ticker}|2"},
        ],
        [
            {"text": "Edit Stop1", "callback_data": f"strategy_stop_trigger_menu|{ticker}|1"},
            {"text": "Edit Stop2", "callback_data": f"strategy_stop_trigger_menu|{ticker}|2"},
        ],
        [
            {"text": "Reset Strategy", "callback_data": f"strategy_reset|{ticker}"},
            {"text": "Reset Fired Flags", "callback_data": f"strategy_reset_fired|{ticker}"},
        ],
        [{"text": "Back", "callback_data": f"view_position|{ticker}"}],
        [{"text": "Home", "callback_data": "main_menu"}],
    ]
    return {"inline_keyboard": rows}


def tp_trigger_text(ticker, level):
    return f"TAKE PROFIT {level}\n\nTicker:\n{ticker}\n\nChoose profit trigger."


def tp_trigger_keyboard(ticker, level):
    rows = []
    for i in range(0, len(TP_TRIGGERS), 3):
        rows.append([
            {"text": f"+{pct}%", "callback_data": f"strategy_tp_sell_menu|{ticker}|{level}|{pct}"}
            for pct in TP_TRIGGERS[i:i+3]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_position|{ticker}"}])
    return {"inline_keyboard": rows}


def tp_sell_text(ticker, level, trigger):
    return f"TAKE PROFIT {level}\n\nTicker:\n{ticker}\n\nTrigger:\n+{trigger}%\n\nHow much of the position do you want to sell?"


def tp_sell_keyboard(ticker, level, trigger):
    rows = []
    for i in range(0, len(SELL_PCTS), 3):
        rows.append([
            {"text": f"Sell {pct}%", "callback_data": f"strategy_set_tp|{ticker}|{level}|{trigger}|{pct}"}
            for pct in SELL_PCTS[i:i+3]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_tp_trigger_menu|{ticker}|{level}"}])
    return {"inline_keyboard": rows}


def dip_trigger_text(ticker, level):
    return f"BUY DIP {level}\n\nTicker:\n{ticker}\n\nChoose drop trigger."


def dip_trigger_keyboard(ticker, level):
    rows = []
    for i in range(0, len(DIP_TRIGGERS), 3):
        rows.append([
            {"text": f"-{pct}%", "callback_data": f"strategy_dip_amount_menu|{ticker}|{level}|{pct}"}
            for pct in DIP_TRIGGERS[i:i+3]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_position|{ticker}"}])
    return {"inline_keyboard": rows}


def dip_amount_text(ticker, level, trigger):
    return f"BUY DIP {level}\n\nTicker:\n{ticker}\n\nTrigger:\n-{trigger}%\n\nHow much should the bot buy?"


def dip_amount_keyboard(ticker, level, trigger):
    rows = []
    for i in range(0, len(BUY_AMOUNTS), 2):
        rows.append([
            {"text": f"${amt}", "callback_data": f"strategy_set_dip|{ticker}|{level}|{trigger}|{amt}"}
            for amt in BUY_AMOUNTS[i:i+2]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_dip_trigger_menu|{ticker}|{level}"}])
    return {"inline_keyboard": rows}


def stop_trigger_text(ticker, level):
    return f"STOP LOSS {level}\n\nTicker:\n{ticker}\n\nChoose loss trigger."


def stop_trigger_keyboard(ticker, level):
    rows = []
    for i in range(0, len(STOP_TRIGGERS), 3):
        rows.append([
            {"text": f"-{pct}%", "callback_data": f"strategy_stop_sell_menu|{ticker}|{level}|{pct}"}
            for pct in STOP_TRIGGERS[i:i+3]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_position|{ticker}"}])
    return {"inline_keyboard": rows}


def stop_sell_text(ticker, level, trigger):
    return f"STOP LOSS {level}\n\nTicker:\n{ticker}\n\nTrigger:\n-{trigger}%\n\nHow much of the position do you want to sell?"


def stop_sell_keyboard(ticker, level, trigger):
    rows = []
    for i in range(0, len(SELL_PCTS), 3):
        rows.append([
            {"text": f"Sell {pct}%", "callback_data": f"strategy_set_stop|{ticker}|{level}|{trigger}|{pct}"}
            for pct in SELL_PCTS[i:i+3]
        ])
    rows.append([{"text": "Back", "callback_data": f"strategy_stop_trigger_menu|{ticker}|{level}"}])
    return {"inline_keyboard": rows}
