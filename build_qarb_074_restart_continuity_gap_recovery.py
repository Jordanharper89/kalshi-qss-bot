from pathlib import Path
import py_compile

R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_074_restart_continuity_gap_recovery.py"
T=R/"test_qarb_074_restart_continuity_gap_recovery.py"

M.write_text(r'''from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q73
STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_074_restart_continuity.json")
CHECKPOINT=Path("runtime_state/qseries/qarb_clean_bot/qarb_074_checkpoint.json")
EXECUTION_AUTHORITY=False;PAPER_ONLY=True;GAP_SECONDS=60.0
def _load(p,d):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except Exception:return d
def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def recover(root,now=None):
 root=Path(root);now=time.time() if now is None else float(now);cur=_load(root/q73.STATE,{});old=_load(root/CHECKPOINT,{})
 prior=dict(old.get("snapshot",{}) or {});base=cur if cur.get("tokens") else prior;merged=dict(prior.get("tokens",{}) or {});merged.update(dict(base.get("tokens",{}) or {}))
 last=float(old.get("checkpoint_unix",now));gap=max(0.0,now-last);used=not bool(cur.get("tokens"))
 core={"revision":"QARB_074","tokens":merged,"token_count":len(merged),"gap_seconds":gap,"gap_detected":gap>GAP_SECONDS,"recovered_from_checkpoint":used,"continuity_ok":bool(merged),"execution_authority":False}
 core["continuity_hash"]=_hash({"tokens":merged,"source_hash":base.get("content_hash")})
 out=dict(core,observed_unix=now);p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
 snap=dict(base);snap["tokens"]=merged;(root/CHECKPOINT).write_text(json.dumps({"checkpoint_unix":now,"snapshot":snap,"continuity_hash":core["continuity_hash"],"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
 return out
def main():
 x=recover(Path.cwd());print("[QARB-074] RESTART CONTINUITY + GAP RECOVERY");print("[CONTINUITY] tokens=%d gap=%.1fs detected=%s checkpoint_recovery=%s"%(x["token_count"],x["gap_seconds"],x["gap_detected"],x["recovered_from_checkpoint"]));print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
''',encoding="utf-8")

T.write_text(r'''import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_074_restart_continuity_gap_recovery as q
class T(unittest.TestCase):
 def test_restart_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/q.q73.STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"tokens":{"TOK":{"status":"ACTIVE"}},"content_hash":"H"}))
   a=q.recover(r,100);self.assertTrue(a["continuity_ok"]);p.unlink();b=q.recover(r,200);self.assertTrue(b["recovered_from_checkpoint"]);self.assertTrue(b["gap_detected"]);self.assertIn("TOK",b["tokens"])
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

for f in (M,T):py_compile.compile(str(f),doraise=True)
print("[PASS] QARB-074 restart continuity + gap recovery installed")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")