from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/'qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py'
if not CORE.is_file():
    raise SystemExit('[FAIL] QSB-052D core missing')

s=CORE.read_text(encoding='utf-8')

pairs=[
('def simulate(raw,user):','def simulate(raw,user,sigverify=True):'),
('"sigVerify":True','"sigVerify":bool(sigverify)'),
('    kp=keypair();user=str(kp.pubkey())',
 '    kp,user=sim_identity()\n    print("[SIGNER] %s"%("LOCAL_PRIVATE_KEY" if kp is not None else "SIM_ONLY_PUBLIC_KEY"),flush=True)'),
('            msg,unsigned=compile_v0(user,ixs,alts,bh);raw=signed_tx(msg,kp)\n            sim=simulate(raw,user);pnl=sim["pnl"];bps=(pnl/op["start"]*10000 if pnl is not None else None)',
 '            msg,unsigned=compile_v0(user,ixs,alts,bh)\n            raw=signed_tx(msg,kp) if kp is not None else unsigned\n            sim=simulate(raw,user,sigverify=(kp is not None));pnl=sim["pnl"];bps=(pnl/op["start"]*10000 if pnl is not None else None)'),
('            if LIVE_ARM:\n                sig=send(raw);print("[LIVE_BUY_SELL] signature=%s expected_sim_net=%+.9f SOL"%(sig,pnl/1e9),flush=True)\n                best["signature"]=sig\n            else:\n                print("[ARMED_PNL] profitable atomic trade found; set QSB_LIVE_ARM=YES to broadcast",flush=True)',
 '            if LIVE_ARM and kp is not None:\n                sig=send(raw);print("[LIVE_BUY_SELL] signature=%s expected_sim_net=%+.9f SOL"%(sig,pnl/1e9),flush=True)\n                best["signature"]=sig\n            elif LIVE_ARM and kp is None:\n                print("[LIVE_BLOCKED] profitable simulation found but QSB_SOLANA_PRIVATE_KEY is not set",flush=True)\n            else:\n                print("[ARMED_PNL] profitable atomic trade found; simulation completed without requiring private key",flush=True)')
]
for old,new in pairs:
    if old not in s:
        raise SystemExit('[FAIL] expected QSB-052D boundary missing: '+old.splitlines()[0])
    s=s.replace(old,new,1)

anchor='def send(raw):\n    return rpc("sendTransaction",[base64.b64encode(raw).decode(),{"encoding":"base64","skipPreflight":False,"preflightCommitment":"processed","maxRetries":2}])\n\n'
helper='def sim_identity():\n    sec=os.getenv("QSB_SOLANA_PRIVATE_KEY","").strip()\n    if sec:\n        kp=keypair()\n        return kp,str(kp.pubkey())\n    return None,os.getenv("QSB_SOLANA_WALLET","").strip() or "MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"\n\n'
if anchor not in s:
    raise SystemExit('[FAIL] send boundary missing')
s=s.replace(anchor,anchor+helper,1)

CORE.write_text(s,encoding='utf-8')
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/'test_qsb_052e_private_key_gate_repair.py'
TEST.write_text('''import os,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c\n\nclass T(unittest.TestCase):\n def test_sim_without_key(self):\n  a=os.environ.pop("QSB_SOLANA_PRIVATE_KEY",None);b=os.environ.pop("QSB_SOLANA_WALLET",None)\n  try:\n   kp,user=c.sim_identity();self.assertIsNone(kp);self.assertEqual(user,"MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X")\n  finally:\n   if a is not None:os.environ["QSB_SOLANA_PRIVATE_KEY"]=a\n   if b is not None:os.environ["QSB_SOLANA_WALLET"]=b\n  print("[PASS] simulation runs without private key")\n def test_unsigned_sim(self):\n  old=c.rpc;seen={}\n  def fake(m,p):\n   if m=="getBalance":return {"value":1000}\n   seen.update(p[1]);return {"err":None,"accounts":[{"lamports":1100}],"unitsConsumed":1,"logs":[]}\n  c.rpc=fake\n  try:\n   x=c.simulate(b"x","MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X",sigverify=False);self.assertFalse(seen["sigVerify"]);self.assertEqual(x["pnl"],100)\n  finally:c.rpc=old\n  print("[PASS] unsigned atomic simulation uses sigVerify=False")\nif __name__=="__main__":unittest.main(verbosity=2)\n''',encoding='utf-8')
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/'run_qsb_052e_private_key_gate_repair.py'
RUN.write_text('from pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\nrun(Path.cwd())\n',encoding='utf-8')
py_compile.compile(str(RUN),doraise=True)

print('[PASS] QSB-052E private-key gate repair installed')
print('[FIX] discovery + atomic simulation no longer require private key')
print('[LIVE] private key required only for actual broadcast')
print('[JUPITER] NONE')
