def detect_sport(text):
    text = str(text or "").lower()

    if any(x in text for x in [
        "mlb", "pro baseball", "baseball",
        "american league", "national league",
        "homerun", "home run", "runs leader",
        "player of the month"
    ]):
        return "mlb"

    if any(x in text for x in [
        "world cup", "fifa", "soccer",
        "premier league", "champions league",
        "goal", "goals", "penalty", "host nation"
    ]):
        return "soccer"

    if any(x in text for x in [
        "nfl", "pro football", "football",
        "super bowl", "touchdown", "passing yards",
        "receiving", "defensive player", "comeback player"
    ]):
        return "nfl"

    if any(x in text for x in [
        "nba", "pro basketball", "basketball",
        "wnba", "western conference", "eastern conference",
        "finals", "points", "all star"
    ]):
        return "nba"

    if any(x in text for x in [
        "nhl", "hockey", "stanley cup",
        "calder", "jack adams", "goals", "saves"
    ]):
        return "nhl"

    if any(x in text for x in [
        "tennis", "wimbledon", "us open",
        "australian open", "french open",
        "atp", "wta", "zverev", "nadal", "djokovic",
        "sinner", "alcaraz"
    ]):
        return "tennis"

    if any(x in text for x in [
        "golf", "masters", "pga", "us open golf",
        "ryder cup", "liv golf"
    ]):
        return "golf"

    if any(x in text for x in [
        "ufc", "mma", "fight", "method of finish",
        "knockout", "submission"
    ]):
        return "mma"

    if any(x in text for x in [
        "rugby", "lacrosse", "cricket", "esports",
        "valorant", "teamfight tactics"
    ]):
        return "other_sports"

    return "generic_sports"


if __name__ == "__main__":
    tests = [
        "World Cup Best Performing Host Nation",
        "Pro Baseball Player of the Month",
        "AP Pro Football Defensive Player Of The Year",
        "Pro Basketball Western Conference Champion",
        "NHL Jack Adams Award",
        "UFC Method of Finish",
        "Alexander Zverev tennis match",
    ]

    for test in tests:
        print(test, "=>", detect_sport(test))