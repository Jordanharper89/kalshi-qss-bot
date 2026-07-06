from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_oracle_why.py")
backup.write_text(text, encoding="utf-8")

needle = '''    if data.startswith("oracle_signal|"):'''

insert = '''    if data.startswith("oracle_why|"):
        ticker = data.split("|", 1)[1]
        from oracle_telegram import oracle_why_text, oracle_signal_decision_keyboard, get_signal_by_ticker
        from oracle.engines.trade_decision import decide_trade

        answer_callback(callback_id, "Oracle why")
        signal = get_signal_by_ticker(ticker)
        action = "PASS"

        if signal:
            decision = decide_trade(
                signal.get("yes_price"),
                signal.get("no_price"),
                signal.get("oracle_fair_value"),
                signal.get("confidence_score"),
            )
            action = decision.get("action", "PASS")

        edit_message(chat_id, message_id, oracle_why_text(ticker), reply_markup=oracle_signal_decision_keyboard(ticker, action))
        return

'''

if insert.strip() not in text:
    text = text.replace(needle, insert + needle, 1)

path.write_text(text, encoding="utf-8")

print("Patched Oracle Why callback.")
print("Backup saved as telegram_bot_backup_before_oracle_why.py")