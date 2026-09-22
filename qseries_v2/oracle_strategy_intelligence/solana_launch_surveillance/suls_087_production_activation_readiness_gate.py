from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 c=json.loads((b/"osi_child_binding_contract.json").read_text(encoding="utf-8"))
 p=json.loads((b/"bounded_osi_child_physical_probe.json").read_text(encoding="utf-8"))
 ready=bool(c.get("syntax_ok") and c.get("suls_imported") and c.get("daemon_thread")
  and p.get("suls_connected") and int(p.get("ack_count",0))>=2 and int(p.get("notifications",0))>0)
 return {"revision":"SULS_087","existing_osi_child_bound":bool(c.get("suls_imported")),
  "bounded_physical_probe_passed":bool(p.get("suls_connected")),
  "production_activation_ready":ready,
  "top_level_launcher_already_has_osi_child":True,
  "top_level_launcher_change_required":False,
  "production_24x7_active":False,
  "fresh_birth_physical_certified":False,
  "profitability_claimed":False,
  "next_required_boundary":"SULS_088_TOP_LEVEL_ORACLE_LIVE_RUNTIME_ACTIVATION_AND_STATUS_CERTIFICATION",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/production_activation_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
