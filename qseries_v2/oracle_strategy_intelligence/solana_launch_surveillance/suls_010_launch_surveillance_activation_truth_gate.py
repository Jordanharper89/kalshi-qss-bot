from __future__ import annotations
import json
def gate(root):
 lat=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/discovery_latency_truth_gate.json").read_text(encoding="utf-8"))
 native=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/native_event_source_resolver.json").read_text(encoding="utf-8"))
 nxt="SULS_011_PHYSICAL_NATIVE_POOL_BIRTH_ACTIVATION" if native.get("native_event_candidate_found") else "SULS_011_NATIVE_SOLANA_BIRTH_SENSOR_FOUNDATION"
 return {"revision":"SULS_010","dexscreener_role":lat.get("classified_role"),
 "native_event_candidate_found":native.get("native_event_candidate_found"),"best_candidate":native.get("best_candidate"),
 "high_frequency_activation_ready":False,"next_required_boundary":nxt,"execution_authority":False}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
