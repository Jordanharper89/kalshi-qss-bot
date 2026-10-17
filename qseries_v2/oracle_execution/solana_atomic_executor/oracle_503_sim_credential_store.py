from __future__ import annotations
"""ORACLE-503 Windows Credential Manager signer storage.

Generic Credential (type 1), CURRENT_USER access, persistent on this PC.
Secrets are never written to repository files or displayed in logs.
NOT a hardware wallet or protection from malware running as this user.
"""
import ctypes
from ctypes import wintypes
import json
import os

TARGET='QSeriesOracle/ORACLE503_SimulationSigner_v1'
TYPE=1
PERSIST=2

class VaultHold(RuntimeError): pass

class Credential(ctypes.Structure):
    _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),
        ('TargetName',wintypes.LPWSTR),('Comment',wintypes.LPWSTR),
        ('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),
        ('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),
        ('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),
        ('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]

class WindowsCredentials:
    def __init__(self):
        if os.name!='nt':raise VaultHold('WINDOWS_CREDENTIAL_MANAGER_REQUIRED')
        self.api=ctypes.WinDLL('Advapi32.dll',use_last_error=True)
        self.api.CredWriteW.argtypes=[ctypes.POINTER(Credential),wintypes.DWORD]
        self.api.CredWriteW.restype=wintypes.BOOL
        self.api.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
        self.api.CredReadW.restype=wintypes.BOOL
        self.api.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD]
        self.api.CredDeleteW.restype=wintypes.BOOL
        self.api.CredFree.argtypes=[ctypes.c_void_p]
        self.api.CredFree.restype=None

    def save(self,target,blob):
        if not isinstance(blob,bytes) or len(blob)>2048 or not blob:raise VaultHold('CREDENTIAL_BLOB_INVALID')
        buf=(ctypes.c_ubyte*len(blob)).from_buffer_copy(blob)
        entry=Credential()
        entry.Type=TYPE;entry.TargetName=target
        entry.Comment='Oracle simulation-only wallet credential'
        entry.CredentialBlobSize=len(blob);entry.CredentialBlob=ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte))
        entry.Persist=PERSIST;entry.UserName='ORACLE503'
        if not self.api.CredWriteW(ctypes.byref(entry),0):
            raise VaultHold('WINDOWS_CREDENTIAL_WRITE_FAILED_'+str(ctypes.get_last_error()))

    def load(self,target):
        p=ctypes.POINTER(Credential)()
        if not self.api.CredReadW(target,TYPE,0,ctypes.byref(p)):
            code=ctypes.get_last_error()
            if code==1168:raise VaultHold('NO_SAVED_SIM_SIGNER')
            raise VaultHold('WINDOWS_CREDENTIAL_READ_FAILED_'+str(code))
        try:
            n=int(p.contents.CredentialBlobSize)
            if n<=0 or n>2048:raise VaultHold('SAVED_CREDENTIAL_SIZE_INVALID')
            return ctypes.string_at(p.contents.CredentialBlob,n)
        finally:self.api.CredFree(p)

    def delete(self,target):
        if not self.api.CredDeleteW(target,TYPE,0):
            code=ctypes.get_last_error()
            if code==1168:raise VaultHold('NO_SAVED_SIM_SIGNER')
            raise VaultHold('WINDOWS_CREDENTIAL_DELETE_FAILED_'+str(code))

def _keypair(secret):
    try:
        from solders.keypair import Keypair
        return Keypair.from_base58_string(secret)
    except Exception:raise VaultHold('INVALID_SOLANA_BASE58_PRIVATE_KEY') from None

def save_signer(secret,backend=None):
    secret=secret.strip()
    if not secret:raise VaultHold('EMPTY_SIGNER')
    pair=_keypair(secret)
    public=str(pair.pubkey())
    record={'version':1,'public':public,'secret':secret,'purpose':'simulation_only'}
    store=backend or WindowsCredentials()
    store.save(TARGET,json.dumps(record,separators=(',',':')).encode('utf-8'))
    del pair,record,secret
    return public

def load_signer(backend=None):
    store=backend or WindowsCredentials()
    try:record=json.loads(store.load(TARGET).decode('utf-8'))
    except VaultHold:raise
    except Exception:raise VaultHold('CORRUPTED_SIM_SIGNER_CREDENTIAL') from None
    if not isinstance(record,dict) or record.get('version')!=1 or record.get('purpose')!='simulation_only':
        raise VaultHold('UNRECOGNIZED_SIM_SIGNER_CREDENTIAL')
    secret=record.get('secret');pub=record.get('public')
    if not isinstance(secret,str) or not isinstance(pub,str):raise VaultHold('SIM_SIGNER_FIELDS_INVALID')
    pair=_keypair(secret)
    if str(pair.pubkey())!=pub:raise VaultHold('VAULT_SIGNER_PUBLIC_MISMATCH')
    return pub,secret

def delete_signer(backend=None):
    (backend or WindowsCredentials()).delete(TARGET)

def tests():
    class FakeStore:
        value=None
        def save(self,t,v):self.value=(t,v)
        def load(self,t):
            if self.value is None:raise VaultHold('NO_SAVED_SIM_SIGNER')
            assert self.value[0]==t
            return self.value[1]
        def delete(self,t):
            if self.value is None:raise VaultHold('NO_SAVED_SIM_SIGNER')
            self.value=None
    class FakeKey:
        @classmethod
        def from_base58_string(cls,secret):
            if secret!='fixture-secret':raise ValueError('invalid')
            return cls()
        def pubkey(self):return 'fixture-pubkey'
    import sys,types
    from unittest.mock import patch
    solders=types.ModuleType('solders');sub=types.ModuleType('solders.keypair');sub.Keypair=FakeKey
    with patch.dict(sys.modules,{'solders':solders,'solders.keypair':sub}):
        f=FakeStore()
        assert save_signer('fixture-secret',f)=='fixture-pubkey'
        assert load_signer(f)==('fixture-pubkey','fixture-secret')
        row=json.loads(f.value[1]);row['public']='wrong'
        f.value=(TARGET,json.dumps(row).encode())
        try:load_signer(f)
        except VaultHold as e:assert str(e)=='VAULT_SIGNER_PUBLIC_MISMATCH'
        else:raise AssertionError('PUBLIC_MATCH_BYPASSED')
        delete_signer(f)
        try:load_signer(f)
        except VaultHold:pass
        else:raise AssertionError('ERASE_IGNORED')
    assert TARGET.startswith('QSeriesOracle/') and TARGET.count('/')==1
    if os.name=='nt':
        import uuid
        t=TARGET+'_TEST_'+uuid.uuid4().hex
        w=WindowsCredentials()
        w.save(t,b'offline-vault-roundtrip-no-secret')
        try:assert w.load(t)==b'offline-vault-roundtrip-no-secret'
        finally:w.delete(t)
        print('[PASS] WINDOWS_CREDENTIAL_MANAGER_LIVE_ROUNDTRIP_NONSECRET')
    else:print('[SKIP] Windows Credential Manager live roundtrip unavailable on non-Windows')
    print('[PASS] ORACLE503 vault fixtures, public/private pairing, erase, and fail closed')
