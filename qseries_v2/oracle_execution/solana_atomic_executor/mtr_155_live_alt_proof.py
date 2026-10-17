"""MTR155 public ALT proof, bounded discovery and read-only finalized RPC."""
import argparse
import json
import re
from pathlib import Path
from .mtr_154_trusted_alt_rpc_evidence import rpc_table, ALTProofError, base58_decode

ROOT=Path(__file__).resolve().parents[3]
DEFAULT_RPC='https://api.mainnet-beta.solana.com'
# Search only public source files likely to define canonical lookup tables.
SOURCE_NAMES=('alt_manager.py','alt_manager','alt_coverage','universal_extension',
              'mtr_119_canonical_alt_atomic_preflight.py','runtime.py')
PATTERN=re.compile(r'(?<![A-Za-z0-9])[1-9A-HJ-NP-Za-km-z]{32,44}(?![A-Za-z0-9])')

def discover():
    hits={}
    for file in ROOT.rglob('*.py'):
        if any(part.lower() in ('venv','.venv','__pycache__','.git','node_modules') for part in file.relative_to(ROOT).parts):
            continue
        if not any(k in file.name.lower() for k in SOURCE_NAMES):
            continue
        if file.stat().st_size>700000: continue
        for line in file.read_text(encoding='utf-8',errors='replace').splitlines():
            if not any(x in line.lower() for x in ('alt','lookup','table')):
                continue
            for candidate in PATTERN.findall(line):
                try: base58_decode(candidate)
                except ALTProofError: continue
                hits.setdefault(candidate,set()).add(str(file.relative_to(ROOT)))
    return {k:sorted(v) for k,v in sorted(hits.items())}

def run(args=None):
    p=argparse.ArgumentParser()
    p.add_argument('--table',default=None)
    p.add_argument('--rpc',default=DEFAULT_RPC)
    p.add_argument('--discover-only',action='store_true')
    p.add_argument('--min-slot',type=int,default=0)
    a=p.parse_args(args)
    candidates=discover()
    print('[MTR155_ALT_CANDIDATES]',len(candidates))
    for key,paths in candidates.items():
        print('[MTR155_CANDIDATE]',key,'sources=',','.join(paths[:3]))
    # Explicit table required: never blindly trust a regex hit.
    if a.discover_only or not a.table:
        print('[MAINNET_RPC] NOT_CALLED')
        print('[LIVE_ALT_CERTIFIED] FALSE')
        print('[HINT] Supply --table with the confirmed canonical ALT address to run read-only RPC')
        return None
    proof=rpc_table(a.rpc,a.table,min_slot=a.min_slot)
    print('[MTR155_LIVE_ALT] VALIDATED_RPC_RESPONSE')
    print('[MTR155_TABLE]',proof['table'])
    print('[MTR155_FINALIZED_SLOT]',proof['rpc_slot'])
    print('[MTR155_ACCOUNTS]',proof['account_count'])
    print('[MTR155_ACCOUNT_HASH]',proof['raw_sha256'])
    print('[MTR155_ONCHAIN_PROOF] RPC_CONDITIONAL')
    print('[TRANSACTION_LINKED] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF] FALSE')
    print('[PROTECTED_PROFIT] FALSE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    return proof

if __name__=='__main__':
    run()
