"""
Oracle Notification Formatter

ORACLE-023.5

Purpose:
- Format Oracle notifications for Telegram.
- Keep messages short and mobile-friendly.
"""


class OracleNotificationFormatter:

    @staticmethod
    def format(signal):

        ticker = signal.get("ticker", "UNKNOWN")
        title = signal.get("title", "")
        action = signal.get("action", "PASS")
        grade = signal.get("grade", "N/A")

        confidence = signal.get(
            "confidence_score",
            0,
        )

        edge = signal.get(
            "edge",
            0,
        )

        fair_value = signal.get(
            "oracle_fair_value",
            0,
        )

        yes_price = signal.get(
            "yes_price",
            0,
        )

        no_price = signal.get(
            "no_price",
            0,
        )

        return f"""
🔮 ORACLE ALERT

{ticker}

{title}

Action:
{action}

Grade:
{grade}

Confidence:
{confidence:.1f}%

Edge:
{edge:.2f}c

Fair Value:
{fair_value:.1f}c

YES:
{yes_price:.1f}c

NO:
{no_price:.1f}c
""".strip()

    @staticmethod
    def format_batch(signals):

        if not signals:
            return (
                "🔮 ORACLE\n\n"
                "No new opportunities."
            )

        messages = []

        for signal in signals:

            messages.append(
                OracleNotificationFormatter.format(
                    signal
                )
            )

        return "\n\n──────────────\n\n".join(
            messages
        )


oracle_notification_formatter = (
    OracleNotificationFormatter()
)