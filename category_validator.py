def validate_category(category, sport=None, source_strength="None"):
    category = str(category or "").lower()
    sport = str(sport or "").lower()

    if category == "crypto":
        return {
            "valid": True,
            "cap_grade": None,
            "reason": "Crypto allowed with live market/price engine",
        }

    if category == "sports":
        if sport in ["mlb", "soccer"]:
            return {
                "valid": True,
                "cap_grade": None,
                "reason": f"Sports validated through {sport} engine",
            }

        return {
            "valid": False,
            "cap_grade": "NO DATA",
            "reason": f"Sports market skipped: no trusted {sport} engine yet",
        }

    if category == "weather":
        return {
            "valid": True,
            "cap_grade": None,
            "reason": "Weather validated through weather engine",
        }

    if category == "politics":
        return {
            "valid": False,
            "cap_grade": "NO DATA",
            "reason": "Politics skipped until polling/news validation engine is connected",
        }

    if category == "entertainment":
        return {
            "valid": False,
            "cap_grade": "NO DATA",
            "reason": "Entertainment skipped until Billboard/Spotify/box-office engine is connected",
        }

    if category == "tesla_spacex":
        return {
            "valid": False,
            "cap_grade": "NO DATA",
            "reason": "Tesla/SpaceX skipped until official/news validation engine is connected",
        }

    return {
        "valid": False,
        "cap_grade": "NO DATA",
        "reason": "General market skipped: no category-specific engine connected",
    }


if __name__ == "__main__":
    tests = [
        ("sports", "mlb"),
        ("sports", "soccer"),
        ("sports", "nfl"),
        ("politics", None),
        ("weather", None),
        ("crypto", None),
        ("general", None),
    ]

    for category, sport in tests:
        print(category, sport, "=>", validate_category(category, sport))