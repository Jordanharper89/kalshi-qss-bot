from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161e_phase8_live_decoder_callable_certification.py"
TEST=ROOT/"test_usls_161e_phase8_live_decoder_callable_certification.py"

MOD_TEXT=r"""from __future__ import annotations
import importlib,inspect,json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase8_live_exact_trade_decoder_interface_diagnostic.json"
PREFERRED=("decode","normalize","materialize","extract","economic","trade")

def _module_name(path):
 p=str(path).replace("\\","/").removesuffix(".py")
 return p.replace("/",".")

def _score(name,args):
 n=name.lower();s=0
 for i,w in enumerate(PREFERRED):
  if w in n:s+=20-i
 a=" ".join(args).lower()
 for w in ("tx","transaction","signature","row","event","record"):
  if w in a:s+=3
 return s

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 out={};importable=0;callable_count=0
 for fam,hits in d.get("family_decoder_candidates",{}).items():
  candidates=[]
  for hit in hits:
   modname=_module_name(hit["path"])
   try:
    mod=importlib.import_module(modname);import_ok=True;importable+=1
   except Exception as e:
    mod=None;import_ok=False;err=repr(e)
   for f in hit.get("functions",[]):
    fn=getattr(mod,f["name"],None) if mod else None
    iscall=callable(fn)
    if iscall:callable_count+=1
    sig=None
    if iscall:
     try:sig=str(inspect.signature(fn))
     except Exception:sig=None
    candidates.append({"module":modname,"path":hit["path"],"function":f["name"],
     "declared_args":f.get("args") or [],"declared_async":bool(f.get("async")),
     "import_ok":import_ok,"import_error":None if import_ok else err,
     "callable":iscall,"runtime_signature":sig,
     "score":_score(f["name"],f.get("args") or [])})
  candidates.sort(key=lambda x:(not x["callable"],-x["score"],x["module"],x["function"]))
  out[fam]=candidates
 selected={f:(next((x for x in xs if x["callable"]),None)) for f,xs in out.items()}
 ready=[f for f,x in selected.items() if x]
 return {"revision":"USLS_161E","family_callable_candidates":out,
  "selected_callable_by_family":selected,
  "ready_family_count":len(ready),"ready_families":ready,
  "importable_module_hits":importable,"callable_function_hits":callable_count,
  "certification_semantics":"IMPORT_AND_SIGNATURE_ONLY_NO_DECODER_INVOCATION",
  "next_boundary":(
   "LIVE_EXACT_TRADE_ECONOMICS_DISPATCHER_WITH_CERTIFIED_CALLABLES"
   if ready else
   "EXPOSE_CALLABLE_DECODER_INTERFACES"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_live_decoder_callable_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161e_phase8_live_decoder_callable_certification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  summary={f:(None if x is None else {
   "module":x["module"],"function":x["function"],
   "signature":x["runtime_signature"],"score":x["score"]})
   for f,x in d["selected_callable_by_family"].items()}
  print("[STATE]",json.dumps({"ready_family_count":d["ready_family_count"],
   "ready_families":d["ready_families"],
   "importable_module_hits":d["importable_module_hits"],
   "callable_function_hits":d["callable_function_hits"],
   "selected":summary,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["ready_family_count"],0,"NO_IMPORTABLE_CALLABLE_DECODER_INTERFACES")
  self.assertEqual(d["certification_semantics"],
   "IMPORT_AND_SIGNATURE_ONLY_NO_DECODER_INVOCATION")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161E live decoder callable certification")
  print("[PASS] callable imports + exact runtime signatures physically certified without invoking decoders")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
