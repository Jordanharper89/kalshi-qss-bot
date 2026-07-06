from pathlib import Path

root = Path.cwd()

provider_file = root / "oracle_data_provider.py"

if not provider_file.exists():
    print("[ERROR] oracle_data_provider.py not found")
    raise SystemExit

text = provider_file.read_text(encoding="utf-8")

backup = root / "oracle_data_provider.py.oracle032_backup"
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

old = '''class MockKalshiProvider(OracleDataProvider):
    name = "mock_kalshi"

    def fetch(self):
        return {
            "provider": self.name,
            "status": "ok",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "markets": [],
            "signals": [],
            "errors": [],
        }
'''

new = '''class MockKalshiProvider(OracleDataProvider):
    name = "mock_kalshi"

    def fetch(self):
        return {
            "provider": self.name,
            "status": "ok",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "markets": [
                {
                    "ticker": "MOCK-ORACLE-001",
                    "title": "Mock market: Oracle detects undervalued YES",
                    "yes_price": 42,
                    "no_price": 58,
                    "volume": 12500,
                    "liquidity": 3200,
                    "expiration": None,
                },
                {
                    "market_ticker": "MOCK-ORACLE-002",
                    "name": "Mock market: High liquidity watch candidate",
                    "yes": 61,
                    "no": 39,
                    "volume_24h": 28400,
                    "open_interest": 9100,
                    "close_time": None,
                },
                {
                    "id": "MOCK-ORACLE-003",
                    "question": "Mock market: Low-volume risky edge",
                    "price": 27,
                    "total_volume": 900,
                    "depth": 350,
                    "end_date": None,
                },
            ],
            "signals": [],
            "errors": [],
        }
'''

if old not in text:
    print("[ERROR] MockKalshiProvider block not found.")
    print("No changes made.")
    raise SystemExit

text = text.replace(old, new, 1)
provider_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-032 mock market pipeline test installed")