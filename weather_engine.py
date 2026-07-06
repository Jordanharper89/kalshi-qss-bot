from weather_market_parser import parse_weather_market
from weather_forecast_engine import get_open_meteo_forecast, score_temperature_market


def clamp(value, low=1, high=99):
    return max(low, min(high, round(value, 1)))


def weather_probability(
    market_price,
    spread=0,
    move=0,
    volume_24h=0,
    title="",
    series_title="",
):
    parsed = parse_weather_market(title, series_title)

    reasons = []
    reasons.extend(parsed["reasons"])

    if not parsed["valid"]:
        return {
            "bot_probability": market_price,
            "valid": False,
            "component_scores": {},
            "reasons": reasons + ["Weather market could not be parsed"],
        }

    forecast = get_open_meteo_forecast(parsed["city"])
    forecast_result = score_temperature_market(parsed, forecast)

    if not forecast_result["valid"]:
        return {
            "bot_probability": market_price,
            "valid": False,
            "component_scores": {},
            "reasons": reasons + [forecast_result["reason"]],
        }

    forecast_score = forecast_result["forecast_score"]
    confidence_score = forecast_result["confidence_score"]
    time_score = forecast_result["time_score"]

    probability = market_price

    probability += ((forecast_score - 50) * 0.55)
    probability += ((confidence_score - 50) * 0.25)
    probability += ((time_score - 50) * 0.10)

    if spread <= 3:
        probability += 2
        reasons.append("Tight spread")

    if move >= 3:
        probability += 1
        reasons.append("Market movement detected")

    if volume_24h >= 100:
        probability += 1
        reasons.append("Volume confirmation")

    reasons.append(forecast_result["reason"])
    reasons.append(f"Forecast source: {forecast_result['source']}")

    if forecast_score >= 70:
        reasons.append("Strong forecast edge")
    elif forecast_score >= 60:
        reasons.append("Moderate forecast edge")
    elif forecast_score <= 40:
        reasons.append("Forecast against this side")

    return {
        "bot_probability": clamp(probability),
        "valid": True,
        "parsed_market": parsed,
        "component_scores": {
            "forecast_score": forecast_score,
            "confidence_score": confidence_score,
            "time_score": time_score,
            "forecast_temp": forecast_result["forecast_temp"],
        },
        "reasons": reasons,
    }


if __name__ == "__main__":
    tests = [
        {
            "market_price": 43,
            "spread": 2,
            "move": 4,
            "volume_24h": 1000,
            "title": "Will the **high temp in Austin** be 89-90° on Jun 20, 2026?",
            "series_title": "Highest temperature in Austin",
        },
        {
            "market_price": 11,
            "spread": 2,
            "move": 4,
            "volume_24h": 1000,
            "title": "Will the **high temp in Austin** be 93-94° on Jun 20, 2026?",
            "series_title": "Highest temperature in Austin",
        },
    ]

    for test in tests:
        print("-" * 60)
        print(weather_probability(**test))