from __future__ import annotations
"""ORACLE-400 native bridge for ORACLE-399.

Grounded contracts: local ORACLE-370 / 378 / 382 / 054 / 077. Current
source proves quote helpers and UNSIGNED native compilation, not a
certified wallet signer. Reject any attempt to infer signed execution.
No scanner mutation, extra websocket, signing, key access or broadcast.
"""
import argparse
import ast
import base64
import hashlib
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PKG=Path(__file__).resolve().parent
STATE=ROOT/'runtime_state/oracle/final_boss_dual'
REPORT=STATE/'oracle_400_native_bridge.json'
CANARY=10_000_000
SIZES=tuple(range(10_000_000,100_000_001,5_000_000))
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
ORDERS={'PUMP_TO_METEORA':(PUMP,DLMM),'METEORA_TO_PUMP':(DLMM,PUMP)}
ALLOWED={PUMP,DLMM,'11111111111111111111111111111111',
 'ComputeBudget111111111111111111111111111111',
 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'}
NATIVE={'370':('oracle_370_native_atomic_executor.py',('bridge','verify_native_program_sequence','reconcile_transaction')),
 '378':('oracle_378_native_reverse_atomic.py',('_sdk_reverse','quote_reverse_only','require_reverse_sdk_result')),
 '382':('oracle_382_staged_native_capacity.py',('get_current_canonical','reconcile_identity')),
 '054':('oracle_054_reverse_native_handoff.py',('native_reverse_route',)),
 '077':('oracle_077_native_executor.py',('compile_native','simulate_native'))}

class Hold(RuntimeError):pass

def owner():
 from qseries_v2.oracle_execution.solana_atomic_executor import oracle_399_final_boss_execution_owner as x
 return x

def frozen():
 return len(owner().source_hashes())

def native_source_contract():
 result={}
 for number,(name,names) in NATIVE.items():
  path=PKG/name
  if not path.is_file():
   result[number]={'status':'CURRENT_NATIVE_MODULE_MISSING','expected':name};continue
  try:
   tree=ast.parse(path.read_text(encoding='utf-8-sig'))
   found={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
   absent=[n for n in names if n not in found]
   result[number]={'status':'SOURCE_CONTRACT_VISIBLE' if not absent else 'NATIVE_FUNCTIONS_MISSING',
     'absent':absent,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  except (SyntaxError,OSError,UnicodeError):
   result[number]={'status':'NATIVE_SOURCE_PARSE_FAILED'}
 return result

def valid_address(x):
 if not isinstance(x,str) or not 32<=len(x)<=44:return False
 return bool(re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]+',x))

def full_identity(row):
 if not isinstance(row,dict):raise Hold('CANONICAL_EVENT_NOT_MAPPING')
 triple=tuple(row.get(k) for k in ('token','pump_pool','meteora_pool'))
 if not all(valid_address(x) for x in triple):raise Hold('FULL_ONCHAIN_POOL_TRIPLE_REQUIRED')
 return triple

def bind_canonical(row,known,ready,*,now_ns=None):
 """Do not admit a scanner quote unless EXACT pools match fresh native inventory."""
 if not isinstance(row,dict):raise Hold('CANDIDATE_NOT_MAPPING')
 triple=full_identity(row)
 if triple not in {tuple(t) for t in known}:raise Hold('CANONICAL_NATIVE_POOL_TRIPLE_NOT_FOUND')
 if triple[0] not in set(ready):raise Hold('NATIVE_TEMPLATE_FOR_TOKEN_NOT_READY')
 if row.get('direction') not in ORDERS:raise Hold('DIRECTION_INVALID')
 size=row.get('size_lamports')
 if type(size) is not int or size not in SIZES:raise Hold('SELECTED_SIZE_OUTSIDE_VERIFIED_GRID')
 if type(row.get('gross_lamports')) is not int or row['gross_lamports']<=0:
  raise Hold('NO_GROSS_POSITIVE_CANDIDATE')
 if row.get('scanner_validator')!='PASS':raise Hold('SCANNER_VALIDATOR_PROOF_REQUIRED')
 if type(row.get('source_epoch')) is not int or row['source_epoch']<1:raise Hold('EPOCH_PROOF_MISSING')
 if type(row.get('snapshot_slot')) is not int or row['snapshot_slot']<1:raise Hold('SLOT_PROOF_MISSING')
 # Age MUST be sourced from a monotonic timestamp in the producer clock domain,
 # or from an authenticated scanner age, never from the local read time alone.
 age=row.get('age_ms')
 if isinstance(age,bool) or not isinstance(age,(float,int)) or not 0<=age<=750:
  raise Hold('SCANNER_CANONICAL_SNAPSHOT_STALE_OR_AGE_UNVERIFIED')
 out={k:row[k] for k in ('token','pump_pool','meteora_pool','direction','size_lamports',
         'gross_lamports','source_epoch','snapshot_slot','scanner_validator','age_ms')}
 out['canonical_pool_match']=True
 return owner().validate_candidate(out)

def eligible_best(rows, costs):
 """Choose highest absolute protected lamport profit; never force smallest size."""
 if not isinstance(rows,list):raise Hold('NATIVE_SIZE_QUOTES_NOT_LIST')
 candidates=[]
 for row in rows:
  if not isinstance(row,dict):continue
  size=row.get('size_lamports'); floor=row.get('protected_min_return_lamports')
  if type(size) is not int or size not in SIZES or type(floor) is not int:continue
  if row.get('direction') not in ORDERS:continue
  if row.get('same_bank') is not True or row.get('all_native_accounts') is not True:continue
  if row.get('full_input_consumed') is not True:continue
  c=costs.get(str(size)) if isinstance(costs,dict) else None
  if not isinstance(c,dict):continue
  required=('base_fee','priority_fee','tip','rent','other')
  if not all(type(c.get(k)) is int and c[k]>=0 for k in required):continue
  net=floor-size-sum(c[k] for k in required)
  if net>0:candidates.append((net,-size,dict(row,protected_net_lamports=net)))
 if not candidates:raise Hold('NO_PROTECTED_FEE_POSITIVE_NATIVE_SIZE')
 return max(candidates,key=lambda x:(x[0],x[1]))[2]

def direction_order(programs,direction):
 if direction not in ORDERS:raise Hold('DIRECTION_INVALID')
 if not isinstance(programs,(list,tuple)) or any(not isinstance(v,str) for v in programs):
  raise Hold('NATIVE_PROGRAM_LIST_INVALID')
 if any(p not in ALLOWED for p in programs):raise Hold('UNRECOGNIZED_INSTRUCTION_PROGRAM')
 legs=tuple(p for p in programs if p in (PUMP,DLMM))
 if legs!=ORDERS[direction]:raise Hold('NATIVE_ATOMIC_LEG_ORDER_OR_COUNT_INVALID')
 return True

def alt_raw_keys(lookups,rpc_fn,context_slot):
 """Resolve v0 lookups from actual onchain ALT account data with ONE batched RPC read.

 Resolve writable addresses from ALL tables before read-only, per Solana v0.
 All indexes and lookup account owners are checked against real account bytes.
 """
 if not lookups:return [],[]
 if not callable(rpc_fn) or type(context_slot) is not int or context_slot<1:
  raise Hold('ALT_ONCHAIN_ACCOUNT_RESOLVER_REQUIRED')
 addresses=[str(l.account_key) for l in lookups]
 result=rpc_fn('getMultipleAccounts',[addresses,
       {'encoding':'base64','commitment':'confirmed','minContextSlot':context_slot}])
 if not isinstance(result,dict) or result.get('context',{}).get('slot',0)<context_slot:
  raise Hold('ALT_RPC_CONTEXT_BEHIND_SNAPSHOT')
 accounts=result.get('value')
 if not isinstance(accounts,list) or len(accounts)!=len(lookups):
  raise Hold('ALT_ONCHAIN_ACCOUNT_RESULT_MISSING')
 writable=[];readonly=[]
 for lookup,account in zip(lookups,accounts):
  if not isinstance(account,dict) or account.get('owner')!='AddressLookupTab1e1111111111111111111111111':
   raise Hold('ALT_ACCOUNT_OWNER_NOT_LOOKUP_PROGRAM')
  data=account.get('data')
  if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':
   raise Hold('ALT_ACCOUNT_DATA_NOT_BASE64')
  try:raw=base64.b64decode(data[0],validate=True)
  except (ValueError,TypeError):raise Hold('ALT_ACCOUNT_ENCODING_FAILED') from None
  if len(raw)<56 or (len(raw)-56)%32 or len(raw)>56+256*32:
   raise Hold('ALT_ACCOUNT_WIRE_LAYOUT_INVALID')
  deactivation=int.from_bytes(raw[4:12],'little')
  if deactivation!=2**64-1:raise Hold('ALT_DEACTIVATING_OR_INACTIVE')
  last_extended=int.from_bytes(raw[12:20],'little')
  extension_start=raw[20]
  table=[raw[56+i*32:56+(i+1)*32] for i in range((len(raw)-56)//32)]
  if not table:raise Hold('ALT_TABLE_NO_ADDRESSES')
  for indexes,output in ((lookup.writable_indexes,writable),(lookup.readonly_indexes,readonly)):
   for ix in indexes:
    if type(ix) is not int or ix>=len(table) or ix<0:
     raise Hold('ALT_ACCOUNT_INDEX_OUT_OF_BOUNDS')
    if context_slot<=last_extended and ix>=extension_start:
     raise Hold('ALT_ADDRESS_NOT_WARMED_PAST_EXTENSION_SLOT')
    output.append(table[ix])
 return writable,readonly

def unsigned_v0_witness(raw,direction,wallet,blockhash,*,rpc_alt=None,context_slot=0):
 """Structural V0 proof only; NEVER interpreted as signed simulation."""
 try:
  from solders.message import MessageV0
  from solders.transaction import VersionedTransaction
  from solders.pubkey import Pubkey
 except ImportError:raise Hold('SOLDERS_REQUIRED_FOR_REAL_NATIVE_PACKET') from None
 if not isinstance(raw,bytes) or len(raw)>1232:raise Hold('NATIVE_PACKET_WIRE_OVERFLOW_OR_MISSING')
 try:
  tx=VersionedTransaction.from_bytes(raw)
  if not isinstance(tx.message,MessageV0):raise Hold('NATIVE_PACKET_NOT_V0')
  msg=tx.message
  if str(msg.recent_blockhash)!=blockhash:raise Hold('NATIVE_BLOCKHASH_DRIFT')
  if str(msg.account_keys[0])!=wallet:raise Hold('NATIVE_FEE_PAYER_DRIFT')
  # Lookup indices are checked against live RPC ALT account bytes, not caller guesses.
  wr,rd=alt_raw_keys(msg.address_table_lookups,rpc_alt,context_slot)
  keys=[str(k) for k in msg.account_keys]+[str(Pubkey.from_bytes(v)) for v in wr+rd]
  programs=[]
  for ix in msg.instructions:
   if ix.program_id_index>=len(keys):raise Hold('NATIVE_PROGRAM_INDEX_OUT_OF_RANGE')
   program=keys[ix.program_id_index]
   if program==PUMP and len(ix.accounts)<26:
    raise Hold('PUMP_NEW_FEE_ACCOUNT_LAYOUT_UNVERIFIED')
   if program==DLMM and len(ix.accounts)<17:
    raise Hold('DLMM_BIN_ACCOUNT_LAYOUT_UNVERIFIED')
   programs.append(program)
  direction_order(programs,direction)
  return {'version':'v0','bytes':len(raw),'direction':direction,
          'native_swaps':2,'lookup_count':len(msg.address_table_lookups),
          'resolved_alt_addresses':len(wr)+len(rd),'unsigned_only':True}
 except Hold:raise
 except Exception:raise Hold('NATIVE_V0_DECODE_FAILED') from None

def signed_v0_witness(raw,direction,wallet,blockhash,*,rpc_alt=None,context_slot=0):
 result=unsigned_v0_witness(raw,direction,wallet,blockhash,
                            rpc_alt=rpc_alt,context_slot=context_slot)
 try:
  from solders.transaction import VersionedTransaction
  VersionedTransaction.from_bytes(raw).verify_and_hash_message()
 except Exception:raise Hold('SIGNED_V0_SIGNATURE_VERIFICATION_FAILED') from None
 result.update(unsigned_only=False,cryptographic_signature_valid=True)
 return result

def snapshot_from_382(report):
 """Use the physical ORACLE-382 native cache; never invent pool prefixes."""
 from qseries_v2.oracle_execution.solana_atomic_executor import oracle_382_staged_native_capacity as m
 triple,ready,status=m.get_current_canonical(report)
 if status!='RECENT_CACHED_CANONICAL_SNAPSHOT':
  raise Hold('NATIVE_SNAPSHOT_'+str(status))
 if not triple or not ready:raise Hold('NATIVE_SNAPSHOT_NO_READY_TOKENS')
 return triple,ready

def canonical_event_db():
 """Read-only SQLite canonical bus lookup, no hardcoded guessed schema."""
 paths=[]
 for base in (STATE,ROOT/'runtime_state/oracle'):
  if base.is_dir():
   for glob in ('*.db','*.sqlite','*.sqlite3'):
    paths.extend(base.glob(glob))
 results=[]
 for dbpath in sorted(set(paths))[:20]:
  try:
   with sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro',uri=True,timeout=.2) as db:
    db.execute('PRAGMA query_only=ON')
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'"):
     if not re.fullmatch(r'[A-Za-z_]\\w*',table) or not re.search('event|candidate|queue',table,re.I):continue
     cols=[r[1] for r in db.execute('PRAGMA table_info("'+table+'")')]
     if any(c in cols for c in ('payload_json','event_json','candidate_json')):
      results.append({'database':dbpath.name,'table':table,'columns':sorted(cols)[:15]})
  except (OSError,sqlite3.Error):continue
 return results[:15]

def next_candidate():
 # Do not assert an SQLite payload is authenticated simply because it exists.
 # The actual oracle_365 source validator and event schema are not yet bound.
 raise Hold('SOURCE_365_EVENT_READER_SIGNATURE_NOT_EXPORTED')

def prepare(candidate,latest_blockhash):
 # ORACLE-054 builds an unsigned reverse route given snap/row/templates/rt/q18.
 # ORACLE-077 compiles route to unsigned v0. Actual contexts and both-direction
 # protected quotes have not been supplied by the exported source functions.
 raise Hold('NATIVE_SDK_CONTEXT_AND_19_PROTECTED_QUOTES_NOT_BOUND')

def sign(plan):
 # NEVER use ORACLE-077.simulate_native as a signer. It is explicitly unsigned.
 raise Hold('NO_CERTIFIED_IN_PROCESS_NATIVE_SIGNER')

def simulation_net_lamports(candidate,plan,sim):
 raise Hold('SIGNED_BALANCE_DELTA_NOT_WIRED')

def revalidate(candidate,plan):
 raise Hold('FRESH_CANONICAL_EVENT_REVALIDATION_NOT_WIRED')

def reconcile(candidate,plan,receipt):
 raise Hold('TRANSACTION_SCOPED_WSOL_TOKEN_RECONCILIATION_NOT_WIRED')

def certification():
 return {'dual_leg_v0_verified':False,'signed_sim_verified':False,
         'dynamic_19_sizes_verified':False,'reconciliation_verified':False,
         'status':'HOLD_NOT_LIVE_CERTIFIED'}

def audit():
 try:count=frozen();freeze='PASS'
 except Exception:count=0;freeze='HOLD'
 sources=native_source_contract()
 full=all(v['status']=='SOURCE_CONTRACT_VISIBLE' for v in sources.values())
 result={'build':'ORACLE400','freeze':freeze,'frozen_files_verified':count,
   'native_source_contracts':sources,'native_source_contracts_complete':full,
   'sqlite_event_buses_read_only':canonical_event_db(),
   '19_sizes':len(SIZES),'direction_order_verified_by_code':list(ORDERS),
   'source_event_reader_certified':False,'native_signer_certified':False,
   'signed_sim_certified':False,'execution_authority':False,
   'private_key_used':False,'rpc_calls':0,'new_ws_connections':0,
   'signing':False,'broadcast':False,
   'status':'HOLD_UNBOUND_NATIVE_EVENT_AND_SIGNER_CONTRACT'}
 STATE.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
 return result

def tests():
 assert len(SIZES)==19 and SIZES[0]==10_000_000 and SIZES[-1]==100_000_000
 direction_order([PUMP,DLMM],'PUMP_TO_METEORA')
 direction_order([DLMM,PUMP],'METEORA_TO_PUMP')
 for bad,di in [([PUMP,DLMM],'METEORA_TO_PUMP'),([DLMM,PUMP,PUMP],'METEORA_TO_PUMP'),
                 ([PUMP,'malicious',DLMM],'PUMP_TO_METEORA')]:
  try:direction_order(bad,di);raise AssertionError('bad program graph accepted')
  except Hold:pass
 valid={'token':'1'*40,'pump_pool':'2'*40,'meteora_pool':'3'*40,'direction':'METEORA_TO_PUMP',
  'size_lamports':35_000_000,'gross_lamports':300000,'source_epoch':3,'snapshot_slot':100,
  'age_ms':35,'scanner_validator':'PASS'}
 try:bind_canonical(valid,[('1'*40,'2'*40,'4'*40)],{'1'*40});raise AssertionError('bad pools accepted')
 except Hold as e:assert 'POOL_TRIPLE' in str(e)
 good=bind_canonical(valid,[('1'*40,'2'*40,'3'*40)],{'1'*40})
 assert good['canonical_pool_match'] is True
 sample=[];fees={}
 for amount,end in ((10_000_000,10_150_000),(35_000_000,35_500_000),(100_000_000,100_180_000)):
  sample.append({'size_lamports':amount,'protected_min_return_lamports':end,
   'direction':'PUMP_TO_METEORA','same_bank':True,'all_native_accounts':True,'full_input_consumed':True})
  fees[str(amount)]={'base_fee':5000,'priority_fee':5000,'tip':0,'rent':0,'other':0}
 assert eligible_best(sample,fees)['size_lamports']==35_000_000
 class Lookup:
  account_key='AbcdefGHjkmNPQrsTUVwxyz123456789ABCDEFGHJKL'
  writable_indexes=[0]
  readonly_indexes=[1]
 data=bytearray(56)+b'\x11'*32+b'\x22'*32
 data[4:12]=(2**64-1).to_bytes(8,'little')
 data[12:20]=(2).to_bytes(8,'little')
 def rpc(method,params):
  assert method=='getMultipleAccounts'
  return {'context':{'slot':100},'value':[{'owner':'AddressLookupTab1e1111111111111111111111111',
   'data':[base64.b64encode(data).decode(),'base64']} ]}
 wr,rd=alt_raw_keys([Lookup()],rpc,100)
 assert len(wr)==len(rd)==1 and wr[0]==b'\x11'*32 and rd[0]==b'\x22'*32
 try:alt_raw_keys([Lookup()],None,100);raise AssertionError('ALT proof omitted')
 except Hold:pass
 for fn,args in ((next_candidate,()),(prepare,({},{})),(sign,({},)),
                 (simulation_net_lamports,({},{},{})),(revalidate,({},{})),
                 (reconcile,({},{},{}))):
  try:fn(*args);raise AssertionError('unverified native boundary opened')
  except Hold:pass
 assert certification()['signed_sim_verified'] is False
 print('[PASS] ORACLE400 source-driven native interface, full pool binding, both directions, max protected profit, hold closed')
 print('[SCOPE] Local offline checks ONLY; no live native SDK signing/simulation claim')

def main():
 p=argparse.ArgumentParser()
 group=p.add_mutually_exclusive_group(required=True)
 group.add_argument('--test',action='store_true')
 group.add_argument('--audit',action='store_true')
 a=p.parse_args()
 try:
  if a.test:tests();return 0
  result=audit()
  print('[ORACLE400_AUDIT]',json.dumps(result,sort_keys=True))
  print('[REPORT]',REPORT.relative_to(ROOT))
  print('[ORACLE400_STATUS]',result['status'])
  return 0
 except Exception as e:
  print('[ORACLE400_HOLD]',type(e).__name__)
  return 2

if __name__=='__main__':raise SystemExit(main())
