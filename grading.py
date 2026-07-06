def to_cents(value):
    try:
        return round(float(value) * 100, 1)
    except:
        return 0

def to_float(value):
    try:
        return float(value)
    except:
        return 0

def detect_systems(market):
    text = " ".join([
        str(market.get("title", "")),
        str(market.get("ticker", "")),
        str(market.get("category", "")),
    ]).lower()

    systems = []

    if any(x in text for x in ["nfl", "nba", "mlb", "game", "season"]):
        systems.append("System 1: Momentum")

    if any(x in text for x in ["over", "under", "above", "below"]):
        systems.append("System 2: Overreaction")

    if any(x in text for x in ["weather", "climate", "temperature", "rain"]):
        systems.append("System 3: Information Convergence")

    if any(x in text for x in ["bitcoin", "crypto", "sol", "tesla", "spacex", "sports"]):
        systems.append("System 4: Cross-Market Edge")

    return systems

def grade_market(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last_price = to_cents(market.get("last_price_dollars"))
    previous_price = to_cents(market.get("previous_price_dollars"))

    volume_24h = to_float(market.get("volume_24h_fp"))
    volume_total = to_float(market.get("volume_fp"))

    spread = yes_ask - yes_bid
    price = last_price if last_price > 0 else yes_ask
    move = abs(last_price - previous_price)
    systems = detect_systems(market)

    score = 0
    reasons = []

    if 35 <= price <= 70:
        score += 20
        reasons.append("Tradable probability zone")

    if 0 < spread <= 6:
        score += 20
        reasons.append("Tight spread")

    if volume_24h >= 100 or volume_total >= 5000:
        score += 20
        reasons.append("Strong volume")

    if move >= 2:
        score += 15
        reasons.append("Recent movement")

    if systems:
        score += 15
        reasons.append("System match")

    if "System 4: Cross-Market Edge" in systems:
        score += 10
        reasons.append("Cross-market edge")

    if score >= 90 and spread <= 3 and volume_24h >= 500:
        grade = "A+"
    elif score >= 80 and spread <= 5 and volume_24h >= 100:
        grade = "A"
    elif score >= 70 and spread <= 6:
        grade = "A-"
    else:
        grade = "PASS"

    return {
        "grade": grade,
        "score": score,
        "price": price,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "spread": spread,
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "systems": systems,
        "reasons": reasons,
        "liquidity": 0,
        "move": move
    }