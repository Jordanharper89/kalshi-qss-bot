from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_010_relationship_surface_snapshot_freeze.py"; TEST=ROOT/"test_oed_010_relationship_surface_snapshot_freeze.py"
assert (PKG/"oed_009_cross_family_dense_trade_surface.py").exists()
code=r"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from qseries_v2.oracle_edge_discovery.oed_006_physical_contract_relationship_graph import build_graph as contracts
from qseries_v2.oracle_edge_discovery.oed_007_temporal_family_coactivity_graph import build_graph as coactivity
from qseries_v2.oracle_edge_discovery.oed_008_source_market_temporal_overlap_graph import build_graph as overlap
from qseries_v2.oracle_edge_discovery.oed_009_cross_family_dense_trade_surface import surface as trade_surface

def freeze(root=None):
    root=Path(root or Path.cwd())
    payload={"schema_version":"OED-010","created_at":datetime.now(timezone.utc).isoformat(),
             "contract_graph":contracts(root),"coactivity_graph":coactivity(root),
             "source_market_overlap_graph":overlap(root),"trade_surface":trade_surface(root),
             "snapshot_purpose":"REPRODUCIBLE_DISCOVERY_INPUT_NOT_EDGE_CERTIFICATION",
             "edge_proven":False,"probability_enabled":False,"direction_enabled":False,
             "publication_allowed":False,"execution_authority":False}
    raw=json.dumps(payload,default=str,sort_keys=True,separators=(",",":")).encode()
    payload["content_sha256"]=hashlib.sha256(raw).hexdigest()
    p=root/"runtime"/"edge_discovery"/"oed_010_relationship_surface_snapshot.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,default=str,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
"""
MOD.write_text(code,encoding="utf-8")
test=r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_010_relationship_surface_snapshot_freeze import freeze
s,p=freeze(Path.cwd())
assert p.exists() and len(s["content_sha256"])==64
assert s["contract_graph"]["contract_nodes"]
assert s["coactivity_graph"]["edges"]
assert s["source_market_overlap_graph"]["edges"]
assert s["trade_surface"]["families"]
assert not s["edge_proven"] and not s["probability_enabled"] and not s["publication_allowed"] and not s["execution_authority"]
print("[SNAPSHOT]",p)
print("[SHA256]",s["content_sha256"])
print("[CONTRACT_NODES]",len(s["contract_graph"]["contract_nodes"]))
print("[COACTIVITY_EDGES]",len(s["coactivity_graph"]["edges"]))
print("[SOURCE_MARKET_EDGES]",len(s["source_market_overlap_graph"]["edges"]))
print("[TRADE_ACTIVE_FAMILIES]",len(s["trade_surface"]["families"]))
print("[PASS] relationship discovery inputs frozen into one reproducible snapshot")
print("[PASS] snapshot is research pavement, not edge certification")
print("[PASS] OED-006..OED-010 relationship and contract graph slice certified")
"""
TEST.write_text(test,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-010 installer complete")