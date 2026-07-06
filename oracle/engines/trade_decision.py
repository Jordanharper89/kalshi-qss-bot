def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, value))


def _to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def decide_trade(yes_price, no_price, oracle_fair_value, confidence_score):
    yes_price = _to_float(yes_price)
    no_price = _to_float(no_price)
    oracle_fair_value = _to_float(oracle_fair_value)
    confidence_score = _to_float(confidence_score)

    yes_fair = clamp(oracle_fair_value)
    no_fair = clamp(100 - oracle_fair_value)

    yes_edge = yes_fair - yes_price
    no_edge = no_fair - no_price

    if confidence_score < 60:
        action = "PASS"
        bias = "NONE"
        selected_edge = max(yes_edge, no_edge)
        reason = "Confidence too low"
    elif yes_edge >= 3 and yes_edge >= no_edge:
        action = "BUY YES"
        bias = "YES"
        selected_edge = yes_edge
        reason = "YES is undervalued versus Oracle fair value"
    elif no_edge >= 3 and no_edge > yes_edge:
        action = "BUY NO"
        bias = "NO"
        selected_edge = no_edge
        reason = "NO is undervalued versus Oracle fair value"
    else:
        action = "PASS"
        bias = "NONE"
        selected_edge = max(yes_edge, no_edge)
        reason = "No tradeable edge"

    if bias == "YES":
        suggested_entry = f"{round(yes_price, 2)}c or better"
        max_entry = round(clamp(yes_fair - 1), 2)
        take_profit = f"{round(clamp(yes_fair), 2)}c-{round(clamp(yes_fair + 3), 2)}c"
        stop_rule = "Exit if YES edge falls below 1c or price breaks 5c below entry"
        expected_hold = "Short-term / active monitor"
    elif bias == "NO":
        suggested_entry = f"{round(no_price, 2)}c or better"
        max_entry = round(clamp(no_fair - 1), 2)
        take_profit = f"{round(clamp(no_fair), 2)}c-{round(clamp(no_fair + 3), 2)}c"
        stop_rule = "Exit if NO edge falls below 1c or price breaks 5c below entry"
        expected_hold = "Short-term / active monitor"
    else:
        suggested_entry = "No entry"
        max_entry = None
        take_profit = "No target"
        stop_rule = "Avoid unless edge improves"
        expected_hold = "No trade"

    return {
        "bias": bias,
        "action": action,
        "yes_edge": round(yes_edge, 2),
        "no_edge": round(no_edge, 2),
        "selected_edge": round(selected_edge, 2),
        "suggested_entry": suggested_entry,
        "max_entry": max_entry,
        "take_profit": take_profit,
        "stop_rule": stop_rule,
        "expected_hold": expected_hold,
        "confidence_score": round(confidence_score, 2),
        "reason": reason,
    }


if __name__ == "__main__":
    print(decide_trade(80, 21, 84, 94))