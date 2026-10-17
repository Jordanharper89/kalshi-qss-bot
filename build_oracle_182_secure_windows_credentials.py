
"""ORACLE182: persist Oracle credentials in Windows Credential Manager.
Run --setup once, then --run181 (or --run-secure) without re-entering keys.
Never writes secrets to a repository file or the Windows environment registry.
"""
import argparse
import ctypes
import getpass
import os
import subprocess
import sys
from ctypes import wintypes
from urllib.parse import quote

HELIUS = 'QSeries.Oracle.HeliusAPI.v1'
SOLANA = 'QSeries.Oracle.SolanaPrivateKey.v1'
RUN181 = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle181_direct_swap2_certification'
SECURE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle156_secure_native_sim_launcher'

class FILETIME(ctypes.Structure):
    _fields_ = [('low', wintypes.DWORD), ('high', wintypes.DWORD)]

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
        ('LastWritten', FILETIME), ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]

def api():
    if os.name != 'nt':
        raise RuntimeError('ORACLE182_REQUIRES_WINDOWS_CMD')
    dll = ctypes.WinDLL('Advapi32', use_last_error=True)
    dll.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
    dll.CredWriteW.restype = wintypes.BOOL
    dll.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                              wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    dll.CredReadW.restype = wintypes.BOOL
    dll.CredFree.argtypes = [ctypes.c_void_p]
    dll.CredFree.restype = None
    return dll

def store(dll, target, secret):
    data = secret.encode('utf-8')
    if not 1 <= len(data) <= 2560:
        raise RuntimeError('ORACLE182_INVALID_SECRET_LENGTH')
    blob = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    entry = CREDENTIAL()
    entry.Type = 1
    entry.TargetName = target
    entry.UserName = 'QSeriesOracle'
    entry.Persist = 2
    entry.CredentialBlobSize = len(data)
    entry.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    try:
        if not dll.CredWriteW(ctypes.byref(entry), 0):
            raise OSError(ctypes.get_last_error(), 'ORACLE182_CREDENTIAL_WRITE_FAILED')
    finally:
        ctypes.memset(ctypes.addressof(blob), 0, len(data))

def load(dll, target):
    ptr = ctypes.POINTER(CREDENTIAL)()
    if not dll.CredReadW(target, 1, 0, ctypes.byref(ptr)):
        error = ctypes.get_last_error()
        if error == 1168:
            return None
        raise OSError(error, 'ORACLE182_CREDENTIAL_READ_FAILED')
    try:
        entry = ptr.contents
        if not 1 <= entry.CredentialBlobSize <= 2560:
            raise RuntimeError('ORACLE182_INVALID_STORED_CREDENTIAL')
        return ctypes.string_at(entry.CredentialBlob,
                                entry.CredentialBlobSize).decode('utf-8')
    finally:
        dll.CredFree(ctypes.cast(ptr, ctypes.c_void_p))

def setup():
    dll = api()
    print('[ORACLE182] Enter credentials privately. Blank keeps existing value.')
    for target, label in [(HELIUS, 'Helius API key'),
                          (SOLANA, 'Solana private key')]:
        existing = load(dll, target) is not None
        value = getpass.getpass(label + ' (hidden; Enter to keep existing): ').strip()
        if value:
            store(dll, target, value)
            print('[STORED]', label, 'in Windows Credential Manager')
        elif existing:
            print('[PRESERVED]', label, 'unchanged')
        else:
            raise RuntimeError('ORACLE182_REQUIRED_CREDENTIAL_MISSING')
    print('[ORACLE182_SETUP_PASS] saved for this Windows user on this computer')

def status():
    dll = api()
    for target, label in [(HELIUS, 'HELIUS'), (SOLANA, 'SOLANA')]:
        print('[ORACLE182_STATUS]', label,
              'STORED' if load(dll, target) is not None else 'MISSING')

def launch(which, seconds):
    dll = api()
    helius, solana = load(dll, HELIUS), load(dll, SOLANA)
    if not helius or not solana:
        raise RuntimeError('ORACLE182_CREDENTIALS_MISSING_RUN_SETUP')
    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = solana
    env['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + quote(helius, safe='')
    env['SOLANA_WS_URL'] = 'wss://mainnet.helius-rpc.com/?api-key=' + quote(helius, safe='')
    env['QSB_LIVE_ARM'] = 'NO'
    if which == '181':
        command = [sys.executable, '-m', RUN181, '--run']
    else:
        command = [sys.executable, '-m', SECURE, '--run', '--seconds', str(seconds)]
    print('[ORACLE182_LAUNCH] credentials loaded; secrets hidden; requested_module=', which,
          'QSB_LIVE_ARM=NO', flush=True)
    return subprocess.call(command, env=env)

def test():
    if os.name == 'nt': assert ctypes.sizeof(FILETIME) == 8
    assert 'PRIVATE_KEY' not in HELIUS
    assert RUN181 != SECURE
    assert quote('a&b', safe='') == 'a%26b'
    assert CREDENTIAL._fields_[6][0] == 'CredentialBlob'
    print('[TEST PASS] ORACLE182 credential layout and protected launcher options')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', action='store_true')
    group.add_argument('--setup', action='store_true')
    group.add_argument('--status', action='store_true')
    group.add_argument('--run181', action='store_true')
    group.add_argument('--run-secure', action='store_true')
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    if args.test: test()
    elif args.setup: setup()
    elif args.status: status()
    else: sys.exit(launch('181' if args.run181 else 'secure', args.seconds))
