from qseries_v2.oracle_coinbase_high_frequency.chf_003_canonical_event_normalizer import normalize_message
x={"received_at":"2026-01-01T00:00:00Z","message":{"channel":"market_trades","timestamp":"2026-01-01T00:00:00Z","events":[{"type":"update","trades":[{"trade_id":"1","product_id":"BTC-USD","price":"100","size":"0.1","side":"BUY","time":"2026-01-01T00:00:00Z"}]}]}}
y=normalize_message(x)
assert len(y)==1 and y[0]["product_id"]=="BTC-USD" and y[0]["price"]==100.0
assert y[0]["source_id"]=="source.crypto.hf.coinbase.market_trade"
print("[PASS] CHF-003 canonical event normalizer certified")
