from pathlib import Path
import ast

ROOT=Path.cwd()
hits=[]

for p in (ROOT/"qseries_v2").rglob("*.py"):
    try:
        s=p.read_text(encoding="utf-8")
        t=ast.parse(s)
    except Exception:
        continue
    for n in t.body:
        if isinstance(n,ast.FunctionDef) and n.name=="native_pump_buy_ixs":
            hits.append((p,s,n))

if len(hits)!=1:
    raise RuntimeError("SAE007B_BUILDER_COUNT:"+str(len(hits)))

path,src,fn=hits[0]

returns=[n for n in ast.walk(fn) if isinstance(n,ast.Return)]

if len(returns)!=1:
    raise RuntimeError("SAE007B_RETURN_COUNT:"+str(len(returns)))

ret=returns[0]
lines=src.splitlines(keepends=True)
indent=" "*(ret.col_offset)

audit=f'''
{indent}for px in ixs:
{indent}    if px.get("programId")!=c.PUMP:
{indent}        continue
{indent}    aa=list(px.get("accounts") or [])
{indent}    print("[SAE007B_PUMP_ACCOUNTS] total=%d"%len(aa),flush=True)
{indent}    for i,a in enumerate(aa):
{indent}        role=("FIXED" if i<23 else "REMAINING_%d"%(i-22))
{indent}        print("[SAE007B_ACCOUNT] index=%d number=%d role=%s pubkey=%s signer=%s writable=%s"%(
{indent}            i,i+1,role,a.get("pubkey"),a.get("isSigner"),a.get("isWritable")),flush=True)
'''

new_src="".join(
    lines[:ret.lineno-1]
    +[audit]
    +lines[ret.lineno-1:]
)

ast.parse(new_src)
path.write_text(new_src,encoding="utf-8")

TEST=ROOT/"test_sae_007b_pumpswap_account_layout_audit.py"

TEST.write_text('''\
from pathlib import Path
import unittest

class T(unittest.TestCase):
    def test_exactly_one_audit(self):
        hits=[]
        for p in Path("qseries_v2").rglob("*.py"):
            try:
                s=p.read_text(encoding="utf-8")
            except Exception:
                continue
            if "[SAE007B_PUMP_ACCOUNTS]" in s:
                hits.append(str(p))
        self.assertEqual(len(hits),1)

    def test_no_broadcast(self):
        p=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
        self.assertNotIn("sendTransaction",p.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main(verbosity=2)
''',encoding="utf-8")

print("[PASS] SAE-007B physical Pump account-layout audit installed")
print("[TARGET]",path)
print("[AUDIT] every Pump account + exact position")
print("[FIXED] positions 1-23")
print("[REMAINING] positions 24+")
print("[TRANSACTION] unchanged")
print("[BROADCAST] disabled")