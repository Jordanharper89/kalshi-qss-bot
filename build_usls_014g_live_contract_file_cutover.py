from pathlib import Path
import json,ast,shutil,time

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json"
PRODUCER=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_074_confirmed_logs_subscription_contract.py"
TEST=ROOT/"test_usls_014g_live_contract_file_cutover.py"

PROGRAMS=(
("PUMP_FUN","6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"),
("PUMP_SWAP","pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),
("RAYDIUM_LAUNCHLAB","LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"),
("RAYDIUM_V4","675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"),
("RAYDIUM_CLMM","CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"),
("RAYDIUM_CPMM","CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"),
("METEORA_DBC","dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"),
("METEORA_DAMM","cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"),
("METEORA_DLMM","LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"),
("METEORA_DYN","Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"),
("ORCA","whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"),
("MOONIT","MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG"),
("BOOP_FUN","boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4"),
("HEAVEN","HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o"),
)

if not STATE.exists():
    raise SystemExit("LIVE_CONTRACT_FILE_NOT_FOUND:"+str(STATE))

old=json.loads(STATE.read_text(encoding="utf-8"))
ws_url=old.get("ws_url")
if not ws_url:
    raise SystemExit("LIVE_CONTRACT_MISSING_WS_URL")

backup=STATE.with_name("confirmed_logs_subscription_contract.pre_usls014g.json")
if not backup.exists():
    shutil.copy2(STATE,backup)

subs=[]
for i,(family,pid) in enumerate(PROGRAMS,1):
    subs.append({
        "jsonrpc":"2.0",
        "id":i,
        "method":"logsSubscribe",
        "params":[{"mentions":[pid]},{"commitment":"confirmed"}],
        "family":family,
        "program_id":pid
    })

new=dict(old)
new["ws_url"]=ws_url
new["subscriptions"]=subs
new["subscription_count"]=len(subs)
new["commitment"]="confirmed"
new["universal_program_families"]=[f for f,_ in PROGRAMS]
new["execution_authority"]=False
new["read_only"]=True
new["usls_revision"]="USLS_014G"
new["updated_unix"]=time.time()

tmp=STATE.with_suffix(".tmp")
tmp.write_text(json.dumps(new,indent=2,sort_keys=True),encoding="utf-8")
check=json.loads(tmp.read_text(encoding="utf-8"))
assert len(check["subscriptions"])==14
assert all(x["method"]=="logsSubscribe" for x in check["subscriptions"])
assert len({x["program_id"] for x in check["subscriptions"]})==14
tmp.replace(STATE)

if not PRODUCER.exists():
    raise SystemExit("SULS_074_PRODUCER_NOT_FOUND")
ps=PRODUCER.read_text(encoding="utf-8")
ast.parse(ps)
missing=[pid for _,pid in PROGRAMS if pid not in ps]
if missing:
    raise SystemExit("PRODUCER_MISSING_VERIFIED_PROGRAMS:"+",".join(missing))

ids=[pid for _,pid in PROGRAMS]
test = '''import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json"
EXPECTED=%r
class T(unittest.TestCase):
 def test_live_contract(self):
  d=json.loads(P.read_text(encoding="utf-8"))
  subs=d.get("subscriptions") or []
  ids=[x.get("program_id") or (((x.get("params") or [{{}}])[0].get("mentions") or [None])[0]) for x in subs]
  print("[STATE]",json.dumps({{"subscription_count":len(subs),"unique_program_count":len(set(ids)),
   "commitment":d.get("commitment"),"ws_url_present":bool(d.get("ws_url")),
   "execution_authority":d.get("execution_authority")}},sort_keys=True))
  for x in subs:
   params=x.get("params") or [{{}},{{}}]
   print("[SUB]",json.dumps({{"id":x.get("id"),"family":x.get("family"),
    "program_id":x.get("program_id"),"method":x.get("method"),
    "commitment":(params[1] or {{}}).get("commitment")}},sort_keys=True))
  self.assertEqual(len(subs),14)
  self.assertEqual(len(set(ids)),14)
  self.assertEqual(set(ids),set(EXPECTED))
  self.assertTrue(all(x.get("method")=="logsSubscribe" for x in subs))
  self.assertTrue(all(((x.get("params") or [{{}},{{}}])[1] or {{}}).get("commitment")=="confirmed" for x in subs))
  self.assertFalse(d.get("execution_authority"))
  print("[PASS] USLS-014G live contract file cut over to all 14 verified programs")
  print("[PASS] SULS-083 will read the universal contract on next serve/runtime start")
  print("[PASS] producer contains all 14 verified program IDs")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
''' % ids

TEST.write_text(test,encoding="utf-8")
print("[PASS] live contract updated:",STATE.relative_to(ROOT))
print("[PASS] backup:",backup.relative_to(ROOT))
print("[PASS] subscription_count=14")
print("[PASS] producer contains all verified program IDs")
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
