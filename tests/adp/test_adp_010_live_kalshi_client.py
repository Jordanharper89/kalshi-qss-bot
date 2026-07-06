from qseries_v2.adapters.live_kalshi_client import live_kalshi_client

health = live_kalshi_client.health()

assert health["status"] == "ready"
assert health["authenticated"] is False
assert health["executes_trades"] is False

url = live_kalshi_client.build_url("markets")

assert url.endswith("/markets")

print("[PASS] ADP-010 Live Kalshi Client")
print(health)
print(url)
