"""Read-only on-chain ALT coverage of captured atomic instruction accounts."""
import base64,json,re
from pathlib import Path
from solders.pubkey import Pubkey
from qseries_v2.oracle_execution.solana_atomic_executor.oracle_100_alt_extension_packet_preflight import rpc,inspect
ROOT=Path('runtime_state/oracle/solana_atomic_executor')
TABLE='HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'
AUTHORITY='DshvULBw4foHgiqLksn8H6vHWredDT6mrJBmKLTFJih6'
CAPTURE=ROOT/'alt_public_capture/oracle094_FQTs7tHw8vM9tUCU6PuRB3r6VK835cvMWZBJBHiBXKoq_FULL.json'

def walk(value,found):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('pubkey','address','programId','program_id','key') and isinstance(v,str):
                try:
                    if str(Pubkey.from_string(v))==v: found.add(v)
                except (ValueError,TypeError): pass
            walk(v,found)
    elif isinstance(value,list):
        for v in value: walk(v,found)

def main():
    if not CAPTURE.is_file(): raise RuntimeError('ORACLE094_FULL_CAPTURE_MISSING')
    obj=json.loads(CAPTURE.read_text(encoding='utf-8'))
    found=set();walk(obj,found)
    if len(found)<10: raise RuntimeError('CAPTURE_ACCOUNT_EXTRACTION_INCOMPLETE')
    response=rpc('getAccountInfo',[TABLE,{'encoding':'base64','commitment':'confirmed'}]);info=response.get('value')
    if not info: raise RuntimeError('ALT_NOT_FOUND')
    existing,_=inspect(info,TABLE,[],AUTHORITY)
    matched=sorted(found.intersection(existing));not_covered=sorted(found.difference(existing))
    report={'status':'READ_ONLY_COVERAGE_AUDIT','table':TABLE,'authority':AUTHORITY,'onchain_alt_count':len(existing),'capture_path':str(CAPTURE),'capture_unique_pubkeys':len(found),'capture_covered_count':len(matched),'capture_covered_pubkeys':matched,'capture_not_covered_count':len(not_covered),'capture_not_covered_pubkeys':not_covered,'exact_v0_wire_bytes':None,'exact_compilation_passed':False,'unsigned_atomic_simulation_passed':False,'signing':False,'broadcast':False}
    out=ROOT/'oracle102_existing_alt_coverage.json';out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8');tmp.replace(out)
    print('[ORACLE102_EXISTING_ALT_COVERAGE] '+json.dumps({k:v for k,v in report.items() if not k.endswith('_pubkeys')},sort_keys=True))
    print('[COVERED]',','.join(matched))
    print('[REPORT]',out)
    print('[HOLD] COVERAGE_AUDIT_ONLY; EXACT_V0_COMPILATION_AND_SIMULATION_NOT_CLAIMED')
    print('[BOUNDARY] NO_KEYS_NO_SIGNING_NO_BROADCAST_NO_SCANNER_CHANGE')
if __name__=='__main__': main()
