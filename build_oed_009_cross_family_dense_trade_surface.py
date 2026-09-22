from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_009_cross_family_dense_trade_surface.py"; TEST=ROOT/"test_oed_009_cross_family_dense_trade_surface.py"
assert (PKG/"oed_008_source_market_temporal_overlap_graph.py").exists()
code=r"""
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
"""
MOD.write_text(code,encoding="utf-8")
test=r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_009_cross_family_dense_trade_surface import surface
s=surface(Path.cwd())
assert s["families"]
assert not s["predictive_edge_proven"] and not s["probability_enabled"] and not s["execution_authority"]
print("[TRADE_ACTIVE_FAMILIES]",len(s["families"]))
print("[TOP_PATH_RICH_FAMILIES]")
for x in s["families"][:30]: print(" ",x)
print("[PASS] path-rich families ranked from physical trade density")
print("[PASS] no predictive edge claimed")
print("[PASS] OED-009 cross-family dense-trade surface certified")
"""
TEST.write_text(test,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-009 installer complete")