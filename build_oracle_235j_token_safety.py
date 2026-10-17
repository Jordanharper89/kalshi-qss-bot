"""ORACLE-235J: conservative mint security gate; read-only."""
import argparse
import json
import os
import sqlite3
import urllib.request
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
REGISTRY = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE235J_TOKEN_SAFETY.json'
LEGACY = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'


def assess(mint, account):
    reasons = []
    if not isinstance(account, dict):
        return {'mint': mint, 'status': 'HOLD',
                'reasons': ['MINT_NOT_FOUND']}
    owner = account.get('owner')
    value = account.get('data')
    if owner not in (LEGACY, TOKEN22):
        reasons.append('UNRECOGNIZED_MINT_OWNER')
    if not isinstance(value, dict) or value.get('program') not in (
        'spl-token', 'spl-token-2022'
    ):
        reasons.append('UNRECOGNIZED_PARSED_MINT')
        info = {}
    else:
        info = value.get('parsed', {})
        if not isinstance(info, dict) or info.get('type') != 'mint':
            reasons.append('NOT_MINT_ACCOUNT')
            info = {}
        else:
            info = info.get('info', {})
            if not isinstance(info, dict):
                reasons.append('INVALID_MINT_INFO')
                info = {}
    expected_program = (
        'spl-token' if owner == LEGACY else 'spl-token-2022'
    )
    if isinstance(value, dict) and value.get('program') != expected_program:
        reasons.append('OWNER_PARSER_MISMATCH')
    if info.get('mintAuthority') is not None:
        reasons.append('MINT_AUTHORITY_PRESENT')
    if info.get('freezeAuthority') is not None:
        reasons.append('FREEZE_AUTHORITY_PRESENT')
    if (
        type(info.get('decimals')) is not int
        or not 0 <= info['decimals'] <= 18
    ):
        reasons.append('DECIMALS_UNVERIFIED')
    try:
        supply = int(info.get('supply'))
        if supply <= 0:
            reasons.append('ZERO_OR_UNKNOWN_SUPPLY')
    except (ValueError, TypeError):
        reasons.append('SUPPLY_UNVERIFIED')
    ext = info.get('extensions', [])
    if owner == TOKEN22:
        if not isinstance(ext, list):
            reasons.append('TOKEN22_EXTENSION_FORMAT_UNKNOWN')
            ext = []
        for item in ext:
            typ = (
                item.get('extension')
                if isinstance(item, dict) else None
            )
            if not typ:
                reasons.append('UNIDENTIFIED_EXTENSION')
            else:
                reasons.append('TOKEN22_EXTENSION_' + str(typ))
        # Parsed RPC responses are not a complete TLV audit.
        # Keep Token-2022 execution blocked until fully supported.
        reasons.append('TOKEN22_FULL_EXTENSION_AUDIT_REQUIRED')
    return {
        'mint': mint,
        'token_program': owner,
        'decimals': info.get('decimals'),
        'status': 'HOLD' if reasons else 'PASS_MINT_FIELDS_ONLY',
        'reasons': sorted(set(reasons)),
        'extension_count': (
            len(ext) if isinstance(ext, list) else -1
        )
    }


def fetch(mints, url):
    payload = json.dumps({
        'jsonrpc': '2.0',
        'id': 23510,
        'method': 'getMultipleAccounts',
        'params': [
            mints,
            {'encoding': 'jsonParsed', 'commitment': 'confirmed'}
        ]
    }).encode()
    request = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get('error'):
        raise RuntimeError('HOLD_MINT_RPC_ERROR')
    result = result.get('result') or {}
    slot = (result.get('context') or {}).get('slot')
    values = result.get('value')
    if (
        type(slot) is not int or slot <= 0
        or not isinstance(values, list)
        or len(values) != len(mints)
    ):
        raise RuntimeError('HOLD_MINT_RPC_SCHEMA')
    return slot, values


def run():
    if (
        os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO'
        or os.getenv('QSB_SOLANA_PRIVATE_KEY')
    ):
        raise RuntimeError('HOLD_ARMED_OR_PRIVATE_KEY_ENVIRONMENT')
    url = os.getenv('SOLANA_RPC_URL', '')
    if not url.startswith('https://'):
        raise RuntimeError('HOLD_RPC_URL_MISSING')
    if not REGISTRY.is_file():
        raise RuntimeError('HOLD_REGISTRY_MISSING')

    with closing(sqlite3.connect(
        REGISTRY.resolve().as_uri() + '?mode=ro', uri=True
    )) as c:
        mints = sorted({
            x[0] for x in c.execute(
                'SELECT mint FROM universal_routes'
            )
        })
    if not mints or len(mints) > 100:
        raise RuntimeError('HOLD_MINT_BATCH_LIMIT')

    slot, values = fetch(mints, url)
    rows = [
        assess(mint, account)
        for mint, account in zip(mints, values)
    ]
    counts = dict(Counter(r['status'] for r in rows))
    result = {
        'build': 'ORACLE235J',
        'context_slot': slot,
        'mints_checked': len(rows),
        'outcomes': counts,
        'signing': False,
        'broadcast': False,
        'trade_safe_certified': False,
        'liquidity_gate_certified': False,
        'mriya_certified': False,
        'status': 'HOLD_COMBINED_EXECUTION_SAFETY',
        'tokens': rows
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(result, indent=2), encoding='utf-8'
    )
    print('[ORACLE235J_RESULT]', json.dumps({
        k: v for k, v in result.items() if k != 'tokens'
    }, sort_keys=True))
    for row in rows:
        print('[ORACLE235J_TOKEN]', json.dumps({
            'mint_prefix': row['mint'][:12],
            'status': row['status'],
            'reasons': row['reasons']
        }, sort_keys=True))
    print('[REPORT]', REPORT)


def test():
    def account(
        program=LEGACY,
        freeze=None,
        mintauth=None,
        extensions=None
    ):
        info = {
            'type': 'mint',
            'info': {
                'decimals': 6,
                'supply': '1000000',
                'mintAuthority': mintauth,
                'freezeAuthority': freeze
            }
        }
        if extensions is not None:
            info['info']['extensions'] = extensions
        return {
            'owner': program,
            'data': {
                'program': (
                    'spl-token'
                    if program == LEGACY else 'spl-token-2022'
                ),
                'parsed': info
            }
        }

    assert assess('m', account())['status'] == (
        'PASS_MINT_FIELDS_ONLY'
    )
    assert 'FREEZE_AUTHORITY_PRESENT' in assess(
        'm', account(freeze='authority')
    )['reasons']
    assert 'MINT_AUTHORITY_PRESENT' in assess(
        'm', account(mintauth='authority')
    )['reasons']
    assert assess(
        'm', account(TOKEN22, extensions=[])
    )['status'] == 'HOLD'
    assert any(
        'transferFeeConfig' in x
        for x in assess(
            'm',
            account(TOKEN22, extensions=[
                {'extension': 'transferFeeConfig'}
            ])
        )['reasons']
    )
    assert assess('m', None)['status'] == 'HOLD'
    print(
        '[ORACLE235J_TEST_PASS] '
        'legacy_mint=TRUE freeze=TRUE '
        'mint_authority=TRUE token22_fail_closed=TRUE'
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if a.test:
        test()
    if a.run:
        run()