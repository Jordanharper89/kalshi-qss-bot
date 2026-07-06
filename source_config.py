TRUSTED_SOURCES = {
    "crypto": {
        "primary": [
            "kalshi_market_data",
            "coinbase_btc_eth_sol_price",
            "binance_price_action",
            "coingecko_market_data",
        ],
        "signals": [
            "price_momentum",
            "volume_spike",
            "spread_check",
            "kalshi_mispricing",
        ],
    },

    "sports": {
        "primary": [
            "kalshi_market_data",
            "espn_scoreboard",
            "official_league_schedule",
            "rotowire_lineups",
            "draftkings_odds_reference",
            "fanduel_odds_reference",
        ],
        "signals": [
            "confirmed_lineups",
            "injury_news",
            "starting_pitchers",
            "weather",
            "market_movement",
        ],
    },

    "weather": {
        "primary": [
            "kalshi_market_data",
            "national_weather_service",
            "open_meteo",
            "weather_gov_hourly",
        ],
        "signals": [
            "forecast_shift",
            "temperature_edge",
            "wind_edge",
            "precipitation_edge",
            "market_lag",
        ],
    },

    "politics": {
        "primary": [
            "kalshi_market_data",
            "realclearpolitics",
            "fivethirtyeight",
            "official_polling_sources",
            "major_news_sources",
        ],
        "signals": [
            "poll_movement",
            "news_shock",
            "approval_change",
            "market_lag",
        ],
    },

    "entertainment": {
        "primary": [
            "kalshi_market_data",
            "billboard_charts",
            "spotify_charts",
            "box_office_mojo",
            "official_award_sources",
        ],
        "signals": [
            "chart_movement",
            "release_news",
            "volume_spike",
            "market_lag",
        ],
    },

    "tesla_spacex": {
        "primary": [
            "kalshi_market_data",
            "tesla_investor_relations",
            "spacex_official",
            "sec_filings",
            "major_news_sources",
        ],
        "signals": [
            "delivery_news",
            "launch_schedule",
            "regulatory_news",
            "market_lag",
        ],
    },
}


def get_sources(category):
    category = str(category or "").lower()

    if "crypto" in category:
        return TRUSTED_SOURCES["crypto"]

    if "sport" in category or "mlb" in category or "nba" in category or "nfl" in category or "nhl" in category:
        return TRUSTED_SOURCES["sports"]

    if "weather" in category or "climate" in category or "temp" in category:
        return TRUSTED_SOURCES["weather"]

    if "politic" in category or "election" in category:
        return TRUSTED_SOURCES["politics"]

    if "entertainment" in category or "movie" in category or "song" in category:
        return TRUSTED_SOURCES["entertainment"]

    if "tesla" in category or "spacex" in category:
        return TRUSTED_SOURCES["tesla_spacex"]

    return {
        "primary": ["kalshi_market_data"],
        "signals": ["price", "spread", "volume", "movement"],
    }


if __name__ == "__main__":
    for key in TRUSTED_SOURCES:
        print("-" * 60)
        print(key.upper())
        print(TRUSTED_SOURCES[key])