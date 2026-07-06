from kalshi_api import get_all_markets
import json

markets = get_all_markets(max_pages=1)

print(json.dumps(markets[0], indent=2))