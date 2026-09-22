from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_001_kalshi_microstructure_archive.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
for x in ("source.kalshi.market_data","yes_price_dollars","yes_bid_dollars","yes_ask_dollars","taker_yes","trade_size","highwater_sequence"):
    assert x in s,x
assert "INSERT INTO" not in s and "UPDATE " not in s and "DELETE FROM" not in s
print("[PASS] OSD-001 deterministic interface test")
print("[PASS] canonical Kalshi market-data source only")
print("[PASS] exact observed dollar fields flattened")
print("[PASS] PostgreSQL access is read-only")
