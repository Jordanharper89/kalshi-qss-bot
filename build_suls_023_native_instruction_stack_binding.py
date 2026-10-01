from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_023_native_instruction_stack_binding.py"
TEST=ROOT/"test_suls_023_native_instruction_stack_binding.py"

MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path

INVOKE=re.compile(r"^Program ([1-9A-HJ-NP-Za-km-z]{32,44}) invoke \[(\d+)\]$")
SUCCESS=re.compile(r"^Program ([1-9A-HJ-NP-Za-km-z]{32,44}) success$")
INSTR=re.compile(r"^Program log: Instruction: (.+)$")

def bind_logs(logs):
 stack=[];events=[]
 for line in logs:
  s=str(line)
  m=INVOKE.match(s)
  if m:
   depth=int(m.group(2))
   while len(stack)>=depth:stack.pop()
   stack.append(m.group(1));continue
  m=SUCCESS.match(s)
  if m:
   if stack and stack[-1]==m.group(1):stack.pop()
   continue
  m=INSTR.match(s)
  if m:
   events.append({"program_id":stack[-1] if stack else None,"instruction":m.group(1)})
  elif s.lower().strip()=="program log: create pool":
   events.append({"program_id":stack[-1] if stack else None,"instruction":"create pool"})
 return events

def run(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_candidate_physical_gate.json"
 d=json.loads(src.read_text(encoding="utf-8"));rows=[]
 for c in d.get("candidates",[]):
  ev=bind_logs(c.get("logs") or [])
  birth=[x for x in ev if any(k in x["instruction"].lower() for k in ("create pool","initializepool","initialize_pool","initialize pool"))]
  rows.append({"slot":c.get("slot"),"signature":c.get("signature"),"instruction_events":ev,
   "birth_instruction_events":birth,"exact_program_bound":all(x.get("program_id") for x in birth) and bool(birth)})
 return {"revision":"SULS_023","rows":rows,"bound_birth_count":sum(x["exact_program_bound"] for x in rows),
  "execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_instruction_stack_binding.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_023_native_instruction_stack_binding import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bind(self):
  p,d=write(ROOT);print("[BOUND_BIRTH_COUNT]",d["bound_birth_count"])
  for x in d["rows"]:
   for e in x["birth_instruction_events"]:print("[BIRTH_INSTRUCTION]",json.dumps(e,sort_keys=True))
  if d["bound_birth_count"]==0:self.fail("NO_BIRTH_INSTRUCTION_BOUND_TO_EXACT_PROGRAM")
  print("[PASS] SULS-023 native instruction-stack binding")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-023 NATIVE INSTRUCTION-STACK BINDING");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
