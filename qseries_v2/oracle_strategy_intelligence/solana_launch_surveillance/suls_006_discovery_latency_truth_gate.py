from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_to_oracle_latency.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 mn=d.get("min_seconds");med=d.get("median_seconds")
 launch_grade=bool(mn is not None and mn<=5.0 and med is not None and med<=15.0)
 return {"revision":"SULS_006","measured":d.get("measured",0),"min_seconds":mn,"median_seconds":med,
 "launch_grade_birth_sensor":launch_grade,"classified_role":"PRIMARY_BIRTH_SENSOR" if launch_grade else "ENRICHMENT_DISCOVERY_ONLY",
 "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/discovery_latency_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
