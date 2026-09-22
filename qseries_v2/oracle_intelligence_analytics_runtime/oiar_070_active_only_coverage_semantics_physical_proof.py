from __future__ import annotations
from pathlib import Path
import inspect
from qseries_v2.oracle_pre_settlement_coverage import opc_023_rotating_full_universe_coverage_cycle as opc23
BUILD_ID="OIAR-070"
def contract_probe():
 f=inspect.getsource(opc23._active_markets);fetch=inspect.getsource(opc23.fetch_rotating_open_page);cycle=inspect.getsource(opc23.run_rotating_full_universe_coverage_cycle)
 return {"active_filter_proven":("active" in f.lower()),"status_open_request_absent":('"status":"open"' not in fetch and "'status':'open'" not in fetch),"raw_page_count_preserved":("raw_page_markets" in cycle),"historical_settled_backfill_supported_by_normal_cycle":False}
def physical_probe(root=None):
 root=Path(root or Path.cwd()).resolve();c=contract_probe();state,markets,nxt,raw=opc23.fetch_rotating_open_page(root);nonactive=sum(str(x.get("status") or "").lower()!="active" for x in markets)
 return {**c,"current_page_active_markets":len(markets),"current_page_raw_markets":int(raw),"current_page_nonactive_admitted":nonactive,"read_only":True,"probability_enabled":False,"execution_authority":False}
def verify_oiar_070():
 c=contract_probe();return BUILD_ID=="OIAR-070" and c["active_filter_proven"] and c["status_open_request_absent"] and not c["historical_settled_backfill_supported_by_normal_cycle"]
