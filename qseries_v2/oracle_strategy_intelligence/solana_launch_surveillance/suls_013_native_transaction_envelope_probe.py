from __future__ import annotations
import json,inspect
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_319_solana_transaction_canonical_envelope as env

def audit():
 fn=env.canonical_transaction_envelopes
 sig=str(inspect.signature(fn))
 src=inspect.getsource(fn)
 return {"revision":"SULS_013","signature":sig,"source_excerpt":src[:5000],
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_transaction_envelope_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
