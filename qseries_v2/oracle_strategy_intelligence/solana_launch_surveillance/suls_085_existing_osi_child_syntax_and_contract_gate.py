from __future__ import annotations
import ast,json
def verify(root):
 p=root/"run_osi_solana_intelligence_live.py";src=p.read_text(encoding="utf-8")
 ast.parse(src)
 return {"revision":"SULS_085","syntax_ok":True,
  "suls_imported":"suls_083_persistent_event_driven_runtime" in src,
  "daemon_thread":"OSI-SULS-EventDriven" in src and "daemon=True" in src,
  "existing_stop_contract":"STOP_OSI_LIVE" in src,
  "existing_intake_preserved":"intake_run" in src,
  "execution_authority_false":"EXECUTION_AUTHORITY=False" in src,
  "top_level_launcher_modified":False,"execution_authority":False,"read_only":True}
def write(root):
 d=verify(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/osi_child_binding_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
