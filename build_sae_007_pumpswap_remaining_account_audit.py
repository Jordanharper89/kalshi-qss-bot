from pathlib import Path
import ast

ROOT=Path.cwd()
matches=[]

for p in (ROOT/"qseries_v2").rglob("*.py"):
    try:
        s=p.read_text(encoding="utf-8")
    except Exception:
        continue
    if "def native_pump_buy_ixs" in s and "build_buy_ix.mjs" in s:
        matches.append((p,s))

if len(matches)!=1:
    raise RuntimeError("SAE007_NATIVE_BUILDER_COUNT:"+str([str(x[0]) for x in matches]))

path,src=matches[0]

marker='''    if not any(ix.get("programId")==c.PUMP for ix in ixs):
        raise RuntimeError("PUMP_NATIVE_PROGRAM_IX_MISSING")
    return ixs,int(j.get("baseOut") or 0)
'''

if marker not in src:
    raise RuntimeError("SAE007_NATIVE_RETURN_SEAM_MISSING")

labels=[
"pool","user","global_config","base_mint","quote_mint",
"user_base_token_account","user_quote_token_account",
"pool_base_token_account","pool_quote_token_account",
"protocol_fee_recipient","protocol_fee_recipient_token_account",
"base_token_program","quote_token_program","system_program",
"associated_token_program","event_authority","program",
"coin_creator_vault_ata","coin_creator_vault_authority",
"global_volume_accumulator","user_volume_accumulator",
"fee_config","fee_program"
]

audit='''    names=%r
    for px in ixs:
        if px.get("programId")!=c.PUMP:
            continue
        aa=list(px.get("accounts") or [])
        print("[SAE007_PUMP_ACCOUNTS] total=%%d fixed_idl=23 remaining=%%d"%%(
            len(aa),max(0,len(aa)-23)),flush=True)
        for n,a in enumerate(aa):
            name=names[n] if n<len(names) else "REMAINING_%d"%(n-22)
            print("[SAE007_ACCOUNT] index=%%d number=%%d name=%%s pubkey=%%s signer=%%s writable=%%s"%%(
                n,n+1,name,a.get("pubkey"),a.get("isSigner"),a.get("isWritable")),flush=True)
''' % labels

src=src.replace(
    marker,
    marker.replace(
        '    return ixs,int(j.get("baseOut") or 0)\n',
        audit+'    return ixs,int(j.get("baseOut") or 0)\n'
    ),
    1
)

ast.parse(src)
path.write_text(src,encoding="utf-8")

test=ROOT/"test_sae_007_pumpswap_remaining_account_audit.py"
test.write_text(
'''import inspect,unittest
from pathlib import Path
class T(unittest.TestCase):
    def test_audit_installed(self):
        hits=[]
        for p in Path("qseries_v2").rglob("*.py"):
            try:s=p.read_text(encoding="utf-8")
            except Exception:continue
            if "[SAE007_PUMP_ACCOUNTS]" in s:hits.append(p)
        self.assertEqual(len(hits),1)
    def test_no_broadcast(self):
        s=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction",s)
if __name__=="__main__":
    unittest.main(verbosity=2)
''',
encoding="utf-8"
)

print("[PASS] SAE-007 PumpSwap remaining-account audit installed")
print("[TARGET]",path)
print("[IDL_FIXED] 23")
print("[AUDIT] accounts 24+ printed as REMAINING_n")
print("[TRANSACTION] unchanged")
print("[BROADCAST] disabled")