import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
)

if not BOT_TOKEN:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"

commands = [
    {"command": "menu", "description": "Open Q Series terminal"},
    {"command": "oracle", "description": "Oracle research menu"},
    {"command": "oracle_top", "description": "Top Oracle signals"},
    {"command": "oracle_watch", "description": "Oracle research watchlist"},
    {"command": "oracle_quality", "description": "Oracle data quality"},
    {"command": "check", "description": "Scan ticker or Kalshi link"},
    {"command": "positions", "description": "Open positions"},
    {"command": "orders", "description": "Open orders"},
    {"command": "settings", "description": "Trade settings"},
    {"command": "balance", "description": "Kalshi account balance"},
    {"command": "help", "description": "Command guide"},
]

response = requests.post(url, json={"commands": commands}, timeout=20)

print(response.status_code)
print(response.text)