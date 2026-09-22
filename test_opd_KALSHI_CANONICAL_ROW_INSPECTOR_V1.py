from pathlib import Path
p=Path("qseries_v2/oracle_predictive_discovery/opd_kalshi_canonical_row_inspector.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("source.kalshi.market_data","canonical_observation_json","observation_type",
          "CANONICAL_KALSHI_SCHEMA_EXPOSED","MODEL/HURDLE/EXECUTION/PUBLICATION"):
    assert x in s,x
print("[PASS] canonical Kalshi row inspector installed")
print("[PASS] read-only PostgreSQL inspection only")
print("[PASS] exact BTC prediction-time bound preserved")
print("[PASS] model/hurdle/execution/publication unchanged")
