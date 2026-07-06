import re


CITY_ALIASES = {
    "austin": "Austin, Texas",
    "houston": "Houston, Texas",
    "dallas": "Dallas, Texas",
    "san antonio": "San Antonio, Texas",
    "new york": "New York, New York",
    "nyc": "New York, New York",
    "chicago": "Chicago, Illinois",
    "los angeles": "Los Angeles, California",
    "miami": "Miami, Florida",
    "phoenix": "Phoenix, Arizona",
    "philadelphia": "Philadelphia, Pennsylvania",
    "boston": "Boston, Massachusetts",
    "seattle": "Seattle, Washington",
    "minneapolis": "Minneapolis, Minnesota",
}


def clean_text(text):
    return str(text or "").replace("**", "").strip()


def detect_city(text):
    t = clean_text(text).lower()

    for key, city in CITY_ALIASES.items():
        if key in t:
            return city

    return None


def detect_temp_type(text):
    t = clean_text(text).lower()

    if any(x in t for x in [
        "minimum temperature",
        "lowest temperature",
        "low temperature",
        "low temp",
        "minimum temp",
    ]):
        return "low"

    if any(x in t for x in [
        "maximum temperature",
        "highest temperature",
        "high temperature",
        "high temp",
        "maximum temp",
    ]):
        return "high"

    if "temperature" in t or "temp" in t:
        return "temperature"

    return None


def detect_operator_and_threshold(text):
    t = clean_text(text)

    under_match = re.search(r"<\s*(\d+)", t)
    over_match = re.search(r">\s*(\d+)", t)

    if under_match:
        return "<", int(under_match.group(1))

    if over_match:
        return ">", int(over_match.group(1))

    range_match = re.search(r"(\d+)\s*-\s*(\d+)", t)

    if range_match:
        return "range", (
            int(range_match.group(1)),
            int(range_match.group(2)),
        )

    return None, None


def parse_weather_market(title, series_title=""):
    combined = f"{series_title} {title}".strip()

    city = detect_city(combined)
    temp_type = detect_temp_type(combined)
    operator, threshold = detect_operator_and_threshold(combined)

    valid = city is not None and temp_type is not None and operator is not None

    reasons = []

    if city:
        reasons.append(f"City detected: {city}")
    else:
        reasons.append("City not detected")

    if temp_type:
        reasons.append(f"Temperature type: {temp_type}")
    else:
        reasons.append("Temperature type not detected")

    if operator:
        reasons.append(f"Condition detected: {operator} {threshold}")
    else:
        reasons.append("Temperature condition not detected")

    return {
        "valid": valid,
        "city": city,
        "temp_type": temp_type,
        "operator": operator,
        "threshold": threshold,
        "reasons": reasons,
    }


if __name__ == "__main__":
    tests = [
        ("Will the minimum temperature be <74° on Jun 19, 2026?", "Lowest temperature in Austin"),
        ("Will the maximum temperature be 82-83° on Jun 19, 2026?", "Seattle Maximum Temperature Daily"),
        ("Will the high temp in NYC be <81° on Jun 19, 2026?", ""),
        ("Lowest temperature in Austin", ""),
    ]

    for title, series in tests:
        print("-" * 60)
        print("Title:", title)
        print("Series:", series)
        print(parse_weather_market(title, series))