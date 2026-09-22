from __future__ import annotations
import ast,json
from pathlib import Path

TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
FUNCS=("attribute_forward_outcomes","_price_for_pair")

def _attrs(fn,text):
 out=[]
 for n in ast.walk(fn):
  if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name):
   out.append({"owner":n.value.id,"attribute":n.attr,"line":n.lineno})
 return out

def _dict_keys(fn,text):
 out=[]
 for n in ast.walk(fn):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args:
   k=n.args[0]
   if isinstance(k,ast.Constant) and isinstance(k.value,str):
    out.append({"owner":ast.get_source_segment(text,n.func.value) or "?","key":k.value,"line":n.lineno})
  elif isinstance(n,ast.Subscript):
   k=n.slice
   if isinstance(k,ast.Constant) and isinstance(k.value,str):
    out.append({"owner":ast.get_source_segment(text,n.value) or "?","key":k.value,"line":n.lineno})
 return out

def audit(root:Path)->dict:
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing OAD-314")
 text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
 found={}
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in FUNCS:
   found[n.name]={
    "args":[a.arg for a in n.args.args],
    "attributes":_attrs(n,text),
    "dict_keys":_dict_keys(n,text),
    "source":ast.get_source_segment(text,n)[:5000],
   }
 if "attribute_forward_outcomes" not in found or "_price_for_pair" not in found:
  raise RuntimeError("Required OAD-314 functions missing")
 return {"revision":"OSI_055C","module":TARGET,"functions":found,
  "execution_authority":False,"read_only":True}

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/oad314_case_record_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
