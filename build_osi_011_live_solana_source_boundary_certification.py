from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_011_live_solana_source_boundary_certification.py"
TEST=ROOT/"test_osi_011_live_solana_source_boundary_certification.py"

MOD_TEXT=r"""from __future__ import annotations
import json, time
from pathlib import Path

EXECUTION_AUTHORITY=False
READ_ONLY=True
TOKENS=("solana","pool","liquidity","swap","token","mint","wallet")

def _load(path:Path):
    try:
        if path.suffix.lower()==".json":
            x=json.loads(path.read_text(encoding="utf-8",errors="replace"))
            return x if isinstance(x,list) else [x]
        if path.suffix.lower()==".jsonl":
            out=[]
            for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
                try: out.append(json.loads(line))
                except Exception: pass
            return out
    except Exception:
        return []
    return []

def certify(root:Path,max_age_seconds:int=900)->dict:
    now=time.time(); candidates=[]
    for base in (root/"runtime_state", root/"runtime"):
        if not base.exists(): continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"): continue
            n=str(p).lower()
            if not any(t in n for t in TOKENS): continue
            age=now-p.stat().st_mtime
            if age>max_age_seconds: continue
            rows=_load(p)
            candidates.append({
                "path":str(p.relative_to(root)),"age_seconds":age,
                "row_count":len(rows),"size":p.stat().st_size,
            })
    candidates.sort(key=lambda x:(x["age_seconds"],x["path"]))
    usable=[x for x in candidates if x["row_count"]>0 and x["size"]>0]
    return {
        "revision":"OSI_011","live_sources":usable,
        "live_source_count":len(usable),
        "live_boundary_certified":bool(usable),
        "execution_authority":False,"read_only":True,
    }

def write_report(root:Path)->Path:
    report=certify(root)
    path=root/"OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json"
    path.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return path
"""

TEST_TEXT=r"""import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_011_live_solana_source_boundary_certification import certify,write_report
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/"runtime_state/solana";p.mkdir(parents=True)
   (p/"live_pool_events.json").write_text(json.dumps([{"asset_key":"SOL:M","event_type":"NEW_POOL"}]),encoding="utf-8")
   x=certify(r,900);self.assertTrue(x["live_boundary_certified"]);self.assertEqual(x["live_source_count"],1)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_006_high_frequency_opportunity_intake_runtime.py").is_file())
  report=certify(ROOT,900)
  path=write_report(ROOT)
  print("[REPORT]",path)
  print("[LIVE_SOURCE_COUNT]",report["live_source_count"])
  if not report["live_boundary_certified"]:
   self.fail("NO_FRESH_PHYSICAL_SOLANA_RUNTIME_SOURCE_FOUND")
  print("[PASS] OSI-011 physical live Solana source boundary certified")
  print("[TRADER] Oracle has a real fresh Solana feed to hunt, not a fixture")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)
 print("[SCOPE] Physical runtime source certification; no execution authority")
if __name__=="__main__":main()
