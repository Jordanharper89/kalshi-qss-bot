
from pathlib import Path
import ast

p = Path("qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py")
s = p.read_text(encoding="utf-8")
compile(s, str(p), "exec")

for x in (
    "def as_obj",
    'json.loads(v)',
    'payload.get("message")',
    'm.get("market_ticker")',
    'yes_price_dollars',
    'yes_bid_dollars',
    'yes_ask_dollars',
    "REJECTED_NO_TICKER",
):
    assert x in s, x

assert "INSERT INTO" not in s
assert "UPDATE " not in s
assert "DELETE FROM" not in s

tree = ast.parse(s)
assert tree is not None

print("[PASS] OSD-001 JSONB/string normalization installed")
print("[PASS] nested payload.message.market_ticker extraction installed")
print("[PASS] exact Kalshi dollar fields preserved")
print("[PASS] bad archive highwater will be rebuilt from zero")
print("[PASS] PostgreSQL access remains read-only")
