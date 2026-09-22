
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
