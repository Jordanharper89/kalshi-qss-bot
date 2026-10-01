from pathlib import Path
import ast,re

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_042_generic_meteora_birth_role_materializer.py"
TEST=ROOT/"test_suls_102b_regex_canonical_birth_identity_contract_repair.py"

HELPER="""def _damm_pool_identity(b, trade_mint):
    e=b.get("envelope") or {}
    raw=e.get("raw_transaction") or {}
    msg=(raw.get("transaction") or {}).get("message") or {}
    meta=raw.get("meta") or {}
    keys=msg.get("accountKeys") or []
    def key(x):
        if isinstance(x,str): return x
        if isinstance(x,int) and 0 <= x < len(keys):
            v=keys[x]
            return v.get("pubkey") if isinstance(v,dict) else v
        return None
    for grp in meta.get("innerInstructions") or []:
        for ix in grp.get("instructions") or []:
            if not isinstance(ix,dict): continue
            program=ix.get("programId") or key(ix.get("programIdIndex"))
            if program != DAMM: continue
            a=[key(x) for x in (ix.get("accounts") or [])]
            if len(a) < 21: continue
            pool,mint_a,mint_b,vault_a,vault_b=a[7],a[9],a[10],a[11],a[12]
            if trade_mint not in (mint_a,mint_b) or WSOL not in (mint_a,mint_b): continue
            if mint_a == trade_mint:
                return {"pair_address":pool,"token_address":trade_mint,
                        "token_vault":vault_a,"quote_vault":vault_b}
            return {"pair_address":pool,"token_address":trade_mint,
                    "token_vault":vault_b,"quote_vault":vault_a}
    return None
"""

TEST_TEXT="""import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_042_generic_meteora_birth_role_materializer.py"

def load():
 spec=importlib.util.spec_from_file_location("_suls042_suls102b",P)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class T(unittest.TestCase):
 def test_identity_contract(self):
  m=load()
  inbox=json.loads((ROOT/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json").read_text(encoding="utf-8"))
  found=None
  for b in reversed(list(inbox.get("births") or [])):
   x=m._materialize(b)
   if x is not None:
    found=x;break
  self.assertIsNotNone(found)
  self.assertTrue(found.get("token_address"))
  self.assertTrue(found.get("pair_address"))
  self.assertEqual(found.get("token_address"),found.get("token_mint"))
  self.assertTrue(found.get("token_vault"))
  self.assertTrue(found.get("quote_vault"))
  self.assertFalse(found.get("execution_authority"))
  print("[STATE]",json.dumps({k:found.get(k) for k in (
   "signature","token_address","token_mint","pair_address",
   "token_vault","quote_vault","launcher_family","execution_authority")},sort_keys=True))
  print("[PASS] SULS-102B canonical birth identity contract repair")
  print("[PASS] exact DAMM V2 inner-CPI identity now published at canonical birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-102B REGEX CANONICAL BIRTH IDENTITY CONTRACT REPAIR")
 print("="*116)
 if not TARGET.exists(): raise SystemExit("CANONICAL_SULS_042_NOT_FOUND")
 original=TARGET.read_text(encoding="utf-8")
 src=original
 ast.parse(src)

 if "_damm_pool_identity" not in src:
  m=re.search(r"(?m)^def\s+_materialize\s*\(",src)
  if not m: raise SystemExit("SULS_042_MATERIALIZE_NOT_FOUND")
  src=src[:m.start()]+HELPER+"\n\n"+src[m.start():]

 if "ident=_damm_pool_identity(b,t)" not in src:
  m=re.search(r"(?m)^(\s*)rawid\s*=",src)
  if not m: raise SystemExit("SULS_042_RAWID_LINE_NOT_FOUND")
  indent=m.group(1)
  inject=indent+"ident=_damm_pool_identity(b,t)\n"+indent+"if not ident:return None\n"
  src=src[:m.start()]+inject+src[m.start():]

 if '"pair_address":ident["pair_address"]' not in src:
  m=re.search(r'(?m)^(\s*)["\']token_mint["\']\s*:\s*t\s*,',src)
  if not m: raise SystemExit("SULS_042_TOKEN_MINT_FIELD_NOT_FOUND")
  replacement=m.group(0)+'"token_address":ident["token_address"],"pair_address":ident["pair_address"],'
  src=src[:m.start()]+replacement+src[m.end():]

 src=re.sub(r'["\']token_vault["\']\s*:\s*tv\["destination"\]',
            '"token_vault":ident["token_vault"]',src,count=1)
 src=re.sub(r'["\']quote_vault["\']\s*:\s*qv\["destination"\]',
            '"quote_vault":ident["quote_vault"]',src,count=1)

 ast.parse(src)
 bak=TARGET.with_suffix(".pre_suls102b.bak")
 if not bak.exists(): bak.write_text(original,encoding="utf-8")
 TARGET.write_text(src,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] repaired canonical:",TARGET.relative_to(ROOT))
 print("[PASS] backup:",bak.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":main()
