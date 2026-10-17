import argparse, json, sqlite3, urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from build_oracle_231 import DB, schema

PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def validate(tx, signature, actor):
    if not isinstance(tx, dict):
        return None
    if type(tx.get('slot')) is not int or tx['slot'] <= 0:
        return None

    meta = tx.get('meta')
    transaction = tx.get('transaction') or {}
    msg = transaction.get('message') or {}

    if not isinstance(meta, dict) or meta.get('err') is not None:
        return None

    keys = msg.get('accountKeys', [])
    signatures = transaction.get('signatures', [])

    if signature not in signatures:
        return None

    if not any(
        isinstance(k, dict)
        and k.get('pubkey') == actor
        and k.get('signer') is True
        for k in keys
    ):
        return None

    programs = {
        i.get('programId')
        for i in msg.get('instructions', [])
        if isinstance(i, dict)
    }

    for inner in meta.get('innerInstructions') or []:
        programs.update(
            i.get('programId')
            for i in inner.get('instructions', [])
            if isinstance(i, dict)
        )

    if PUMP not in programs and DLMM not in programs:
        return None

    mints = {
        b.get('mint')
        for group in ('preTokenBalances','postTokenBalances')
        for b in meta.get(group, []) or []
        if isinstance(b, dict) and b.get('mint')
    }

    return {
        'signature': signature,
        'slot': tx['slot'],
        'actor': actor,
        'programs': sorted(
            p for p in programs if isinstance(p, str)
        ),
        'mints': sorted(mints)
    }

def rpc(signature):
    import build_oracle_182_secure_windows_credentials as cred

    key = cred.load(cred.api(), cred.HELIUS)
    if not key:
        raise RuntimeError('HOLD_NO_STORED_HELIUS_CREDENTIAL')

    url = ('https://mainnet.helius-rpc.com/?api-key='
           + quote(key, safe=''))
    del key

    payload = json.dumps({
        'jsonrpc':'2.0',
        'id':1,
        'method':'getTransaction',
        'params':[
            signature,
            {
                'encoding':'jsonParsed',
                'commitment':'confirmed',
                'maxSupportedTransactionVersion':0
            }
        ]
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type':'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as f:
            response = json.load(f)
    except Exception as exc:
        raise RuntimeError(
            'HOLD_RPC_REQUEST_FAILED_' + type(exc).__name__
        ) from None

    if response.get('error'):
        raise RuntimeError('HOLD_RPC_TRANSACTION_ERROR')

    return response.get('result')

def run(signature, actor, path=DB):
    if not signature or not actor:
        raise RuntimeError(
            'HOLD_MRIYA_SIGNER_AND_SIGNATURE_REQUIRED'
        )
    if not path.is_file():
        raise RuntimeError('HOLD_REGISTRY_MISSING')

    evidence = validate(rpc(signature), signature, actor)

    if not evidence or not evidence['mints']:
        print('[ORACLE232_HOLD] '
              'signer_or_program_or_mint_unverified')
        return

    with closing(sqlite3.connect(path,timeout=20)) as c:
        schema(c)
        registered = {
            r[0] for r in c.execute(
                'SELECT mint FROM universal_routes'
            )
        }
        admitted = sorted(
            registered.intersection(evidence['mints'])
        )

    # A valid signature proves an on-chain signer,
    # not independently verified Mriya ownership.
    # No Mriya evidence is admitted without attribution.

    print('[ORACLE232_HOLD] '
          'onchain_signer_verified=TRUE '
          'matched_registered_mints=',len(admitted),
          'mriya_attribution_verified=FALSE')

def test():
    tx = {
        'slot':1,
        'meta':{
            'err':None,
            'innerInstructions':[],
            'preTokenBalances':[{'mint':'M'}]
        },
        'transaction':{
            'signatures':['sig'],
            'message':{
                'accountKeys':[
                    {'pubkey':'actor','signer':True}
                ],
                'instructions':[{'programId':PUMP}]
            }
        }
    }

    assert validate(tx,'sig','actor')['mints'] == ['M']
    assert validate(tx,'sig','other') is None

    tx['meta']['err'] = {'fail':1}
    assert validate(tx,'sig','actor') is None

    print('[ORACLE232_TEST_PASS] '
          'rpc_structure=TRUE signer=TRUE '
          'failed_tx_rejected=TRUE')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--signature')
    p.add_argument('--mriya-signer')
    a = p.parse_args()

    if a.test:
        test()
    if a.signature or a.mriya_signer:
        run(a.signature,a.mriya_signer)