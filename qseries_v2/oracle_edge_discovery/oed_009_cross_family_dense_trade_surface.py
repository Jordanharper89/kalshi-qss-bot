
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_003_kalshi_market_family_physical_inventory import inventory

def surface(root=None):
    s=inventory(Path(root or Path.cwd()))
    out=[]
    for x in s["families"]:
        trades=int(x["types"].get("trade",0)); tickers=int(x["types"].get("ticker",0))
        if trades<=0: continue
        out.append({"family":x["family"],"rows":x["rows"],"contracts":x["contracts"],
                    "trade_rows":trades,"ticker_rows":tickers,"span_seconds":x["span_seconds"],
                    "trades_per_contract":trades/max(1,x["contracts"]),
                    "trade_fraction":trades/max(1,x["rows"])})
    out.sort(key=lambda x:(x["trades_per_contract"],x["trade_rows"],x["contracts"]),reverse=True)
    return {"schema_version":"OED-009","families":out,
            "purpose":"PRIORITIZE_PATH_RICH_FAMILIES_FOR_CROSS_FAMILY_EDGE_TESTS",
            "predictive_edge_proven":False,"probability_enabled":False,"direction_enabled":False,
            "publication_allowed":False,"execution_authority":False}
