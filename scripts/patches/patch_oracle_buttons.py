from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_oracle_buttons.py")
backup.write_text(text, encoding="utf-8")

old = '''        from oracle_telegram import oracle_signal_text, oracle_back_keyboard
        result = oracle_signal_text(ticker)
        send_message(chat_id, result, reply_markup=oracle_back_keyboard())
        return
'''

new = '''        from oracle_telegram import oracle_signal_text, oracle_signal_decision_keyboard
        from oracle.engines.trade_decision import decide_trade
        from oracle_telegram import get_signal_by_ticker
        from oracle.api.ticker_ingest import extract_oracle_ticker

        cleaned = extract_oracle_ticker(ticker)
        result = oracle_signal_text(ticker)
        signal = get_signal_by_ticker(cleaned)

        action = "PASS"
        if signal:
            decision = decide_trade(
                signal.get("yes_price"),
                signal.get("no_price"),
                signal.get("oracle_fair_value"),
                signal.get("confidence_score"),
            )
            action = decision.get("action", "PASS")

        send_message(chat_id, result, reply_markup=oracle_signal_decision_keyboard(cleaned, action))
        return
'''

if old not in text:
    print("Command block not found. No command patch applied.")
else:
    text = text.replace(old, new, 1)

old_cb = '''    if data.startswith("oracle_signal|"):
        ticker = data.split("|", 1)[1]
        from oracle_telegram import oracle_signal_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle signal")
        edit_message(chat_id, message_id, oracle_signal_text(ticker), reply_markup=oracle_back_keyboard())
        return
'''

new_cb = '''    if data.startswith("oracle_signal|"):
        ticker = data.split("|", 1)[1]
        from oracle_telegram import oracle_signal_text, oracle_signal_decision_keyboard, get_signal_by_ticker
        from oracle.engines.trade_decision import decide_trade
        from oracle.api.ticker_ingest import extract_oracle_ticker

        cleaned = extract_oracle_ticker(ticker)
        answer_callback(callback_id, "Oracle signal")
        result = oracle_signal_text(ticker)
        signal = get_signal_by_ticker(cleaned)

        action = "PASS"
        if signal:
            decision = decide_trade(
                signal.get("yes_price"),
                signal.get("no_price"),
                signal.get("oracle_fair_value"),
                signal.get("confidence_score"),
            )
            action = decision.get("action", "PASS")

        edit_message(chat_id, message_id, result, reply_markup=oracle_signal_decision_keyboard(cleaned, action))
        return
'''

if old_cb not in text:
    print("Callback block not found. No callback patch applied.")
else:
    text = text.replace(old_cb, new_cb, 1)

path.write_text(text, encoding="utf-8")

print("Patched Oracle decision buttons.")
print("Backup saved as telegram_bot_backup_before_oracle_buttons.py")