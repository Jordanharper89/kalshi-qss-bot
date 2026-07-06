import os
import winsound

from q1_crypto import find_crypto_events
from qss_elite import get_active_rows, system3_read, final_grade
from system2_overreaction import detect_overreaction


def beep():
    try:
        winsound.Beep(1200, 500)
        winsound.Beep(1600, 500)
    except:
        pass


def run_alert_engine():
    rows = get_active_rows()
    sys3_label, sys3_bonus, sys3_reason = system3_read(rows)

    alerts = []

    for row in rows:
        if row["grade"] == "PASS":
            continue

        if row["yes_ask"] > 75:
            continue

        sys2 = detect_overreaction(row)
        signal = "NORMAL"

        if sys2 and sys2["signal"] != "PASS":
            signal = sys2["signal"]

        elite_score = row["score"] + sys3_bonus

        if signal in ["AVOID CHASE", "LOTTO ZONE"]:
            elite_score -= 20

        grade = final_grade(elite_score)

        if grade not in ["A+", "A"]:
            continue

        alerts.append({
            **row,
            "elite_score": elite_score,
            "elite_grade": grade,
            "signal": signal,
            "system3_label": sys3_label,
            "system3_reason": sys3_reason,
        })

    alerts = sorted(alerts, key=lambda x: x["elite_score"], reverse=True)

    print("\nALERT ENGINE")
    print("-" * 60)

    if not alerts:
        print("No alert-level plays right now.")
        return

    beep()

    for play in alerts[:3]:
        print("-" * 60)
        print("ALERT PLAY")
        print(f"Grade: {play['elite_grade']}")
        print(f"Score: {play['elite_score']}/100")
        print(f"Signal: {play['signal']}")
        print(f"Market: {play['title']}")
        print(f"Symbol: {play['symbol']}")
        print(f"Minutes Left: {play['minutes_left']}")
        print(f"Price: {play['price']}c")
        print(f"Entry: {play['yes_ask']}c")
        print(f"Target: {min(99, play['yes_ask'] + 6)}c")
        print(f"Stop: {max(1, play['yes_ask'] - 4)}c")
        print(f"System 3: {play['system3_label']}")
        print(f"Read: {play['system3_reason']}")


if __name__ == "__main__":
    run_alert_engine()