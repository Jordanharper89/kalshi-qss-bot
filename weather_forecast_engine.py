import requests
import time


GEOCODE = {
    "Austin, Texas": (30.2672, -97.7431),
    "Houston, Texas": (29.7604, -95.3698),
    "Dallas, Texas": (32.7767, -96.7970),
    "San Antonio, Texas": (29.4241, -98.4936),
    "New York, New York": (40.7128, -74.0060),
    "Chicago, Illinois": (41.8781, -87.6298),
    "Los Angeles, California": (34.0522, -118.2437),
    "Miami, Florida": (25.7617, -80.1918),
    "Phoenix, Arizona": (33.4484, -112.0740),
    "Philadelphia, Pennsylvania": (39.9526, -75.1652),
    "Boston, Massachusetts": (42.3601, -71.0589),
    "Seattle, Washington": (47.6062, -122.3321),
    "Minneapolis, Minnesota": (44.9778, -93.2650),
}

FORECAST_CACHE = {}
CACHE_SECONDS = 300


def get_open_meteo_forecast(city):
    now = time.time()

    if city in FORECAST_CACHE:
        cached = FORECAST_CACHE[city]
        if now - cached["time"] <= CACHE_SECONDS:
            result = dict(cached["data"])
            result["cached"] = True
            return result

    if city not in GEOCODE:
        return {
            "valid": False,
            "reason": f"No coordinates found for {city}",
        }

    lat, lon = GEOCODE[city]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
        "forecast_days": 3,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})

        result = {
            "valid": True,
            "city": city,
            "dates": daily.get("time", []),
            "highs": daily.get("temperature_2m_max", []),
            "lows": daily.get("temperature_2m_min", []),
            "source": "Open-Meteo",
            "cached": False,
        }

        if not result["dates"]:
            return {
                "valid": False,
                "reason": "No forecast dates returned",
            }

        FORECAST_CACHE[city] = {
            "time": now,
            "data": result,
        }

        return result

    except Exception as e:
        return {
            "valid": False,
            "reason": str(e),
        }


def score_temperature_market(parsed_market, forecast):
    if not parsed_market.get("valid"):
        return {
            "valid": False,
            "forecast_score": 50,
            "confidence_score": 50,
            "time_score": 50,
            "reason": "Parsed market invalid",
        }

    if not forecast.get("valid"):
        return {
            "valid": False,
            "forecast_score": 50,
            "confidence_score": 50,
            "time_score": 50,
            "reason": forecast.get("reason", "Forecast invalid"),
        }

    temp_type = parsed_market.get("temp_type")
    operator = parsed_market.get("operator")
    threshold = parsed_market.get("threshold")

    if temp_type == "high":
        forecast_temp = forecast["highs"][0]
    elif temp_type == "low":
        forecast_temp = forecast["lows"][0]
    else:
        return {
            "valid": False,
            "forecast_score": 50,
            "confidence_score": 50,
            "time_score": 50,
            "reason": "Unsupported temp type",
        }

    forecast_score = 50
    confidence_score = 60
    time_score = 65

    if operator == "<":
        diff = threshold - forecast_temp
        if diff >= 4:
            forecast_score = 80
        elif diff >= 2:
            forecast_score = 70
        elif diff >= 0:
            forecast_score = 60
        elif diff >= -2:
            forecast_score = 45
        else:
            forecast_score = 30

    elif operator == ">":
        diff = forecast_temp - threshold
        if diff >= 4:
            forecast_score = 80
        elif diff >= 2:
            forecast_score = 70
        elif diff >= 0:
            forecast_score = 60
        elif diff >= -2:
            forecast_score = 45
        else:
            forecast_score = 30

    elif operator == "range":
        low, high = threshold
        if low <= forecast_temp <= high:
            forecast_score = 80
        elif low - 1 <= forecast_temp <= high + 1:
            forecast_score = 68
        elif low - 2 <= forecast_temp <= high + 2:
            forecast_score = 58
        else:
            forecast_score = 35

    cache_note = "cached" if forecast.get("cached") else "live"

    return {
        "valid": True,
        "forecast_temp": forecast_temp,
        "forecast_score": forecast_score,
        "confidence_score": confidence_score,
        "time_score": time_score,
        "reason": f"Forecast {temp_type}: {forecast_temp}°F ({cache_note})",
        "source": forecast.get("source", "unknown"),
    }


if __name__ == "__main__":
    from weather_market_parser import parse_weather_market

    title = "Will the maximum temperature be 89-90° on Jun 20, 2026?"
    series_title = "Highest temperature in Austin"

    parsed = parse_weather_market(title, series_title)

    print(get_open_meteo_forecast(parsed["city"]))
    print(get_open_meteo_forecast(parsed["city"]))
    print(score_temperature_market(parsed, get_open_meteo_forecast(parsed["city"])))