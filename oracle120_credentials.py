"""Persistent Windows Credential Manager storage and launcher for ORACLE-120.

Run once: python oracle120_credentials.py --setup
Then:    python oracle120_credentials.py --run
Secrets remain in Windows Credential Manager, protected by the signed-in Windows user.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import getpass
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

WALLET = "QSeries.Oracle120.SolanaPrivateKey"
HELIUS = "QSeries.Oracle120.HeliusApiKey"
TARGET = Path("qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/run_oracle120.py")
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2

if sys.platform == "win32":
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
            ("LastWritten", FILETIME), ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    ADVAPI = ctypes.WinDLL("Advapi32", use_last_error=True)
    ADVAPI.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    ADVAPI.CredWriteW.restype = wintypes.BOOL
    ADVAPI.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    ADVAPI.CredReadW.restype = wintypes.BOOL
    ADVAPI.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    ADVAPI.CredDeleteW.restype = wintypes.BOOL
    ADVAPI.CredFree.argtypes = [ctypes.c_void_p]
    ADVAPI.CredFree.restype = None


def windows_only():
    if sys.platform != "win32":
        raise RuntimeError("Windows Credential Manager requires Windows")


def store(target: str, secret: str):
    windows_only()
    blob = bytearray(secret.encode("utf-16-le"))
    if not blob or len(blob) > 2560:
        raise ValueError("Credential missing or exceeds Windows Credential Manager limit")
    mem = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    cred = CREDENTIALW()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target
    cred.Comment = "Q Series Oracle 120 (Windows account protected)"
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(mem, ctypes.POINTER(ctypes.c_ubyte))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.UserName = "Oracle120"
    try:
        if not ADVAPI.CredWriteW(ctypes.byref(cred), 0):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        ctypes.memset(ctypes.addressof(mem), 0, len(blob))
        for i in range(len(blob)):
            blob[i] = 0


def retrieve(target: str) -> str | None:
    windows_only()
    ptr = ctypes.POINTER(CREDENTIALW)()
    if not ADVAPI.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(ptr)):
        err = ctypes.get_last_error()
        if err == 1168:  # ERROR_NOT_FOUND
            return None
        raise ctypes.WinError(err)
    try:
        cred = ptr.contents
        if not cred.CredentialBlob or not cred.CredentialBlobSize:
            raise ValueError("Stored credential empty")
        value = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
        return value.decode("utf-16-le")
    finally:
        ADVAPI.CredFree(ptr)


def delete(target: str):
    windows_only()
    if not ADVAPI.CredDeleteW(target, CRED_TYPE_GENERIC, 0):
        err = ctypes.get_last_error()
        if err != 1168:
            raise ctypes.WinError(err)


def configure():
    wallet = getpass.getpass("Solana private key (hidden; stored in Windows Credential Manager): ").strip()
    if not wallet:
        raise ValueError("Empty Solana key; existing credentials unchanged")
    helius = getpass.getpass("Helius API key (hidden; stored in Windows Credential Manager): ").strip()
    if not helius:
        raise ValueError("Empty Helius key; existing credentials unchanged")
    store(WALLET, wallet)
    store(HELIUS, helius)
    del wallet, helius
    if not retrieve(WALLET) or not retrieve(HELIUS):
        raise RuntimeError("Credential read-back failed")
    print("[PASS] Both credentials stored and read back using Windows Credential Manager")
    print("[SCOPE] Available to programs running as your signed-in Windows user")
    print("[NEXT] python oracle120_credentials.py --run")


def launch(once: bool):
    if not TARGET.is_file():
        raise FileNotFoundError(f"ORACLE-120 launcher missing: {TARGET}")
    wallet = retrieve(WALLET)
    helius = retrieve(HELIUS)
    if not wallet or not helius:
        raise RuntimeError("Credential missing; first run python oracle120_credentials.py --setup")
    env = os.environ.copy()
    env["QSB_SOLANA_PRIVATE_KEY"] = wallet
    api = quote(helius, safe="")
    env["SOLANA_RPC_URL"] = "https://mainnet.helius-rpc.com/?api-key=" + api
    env["SOLANA_WS_URL"] = "wss://mainnet.helius-rpc.com/?api-key=" + api
    del wallet, helius, api
    cmd = [sys.executable, str(TARGET), "--watch"]
    if once:
        cmd.append("--once")
    print("[ORACLE-120] Windows credentials loaded; starting Mriya + replenishment + watch", flush=True)
    print("[MODE] WATCH_ONLY (no signing or broadcasting)", flush=True)
    # Secret is in child process environment, never in the command-line arguments.
    return subprocess.call(cmd, env=env)


def main():
    ap = argparse.ArgumentParser(description="ORACLE-120 permanent encrypted Windows credentials")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--setup", action="store_true", help="One-time secure credential entry")
    group.add_argument("--run", action="store_true", help="Start watch without prompts")
    group.add_argument("--status", action="store_true", help="Show presence only, never values")
    group.add_argument("--delete", action="store_true", help="Delete saved credentials")
    ap.add_argument("--once", action="store_true", help="One evaluation cycle with --run")
    args = ap.parse_args()
    try:
        windows_only()
        if args.setup:
            configure()
        elif args.status:
            print("[SOLANA]", "STORED" if retrieve(WALLET) else "MISSING")
            print("[HELIUS]", "STORED" if retrieve(HELIUS) else "MISSING")
        elif args.delete:
            delete(WALLET)
            delete(HELIUS)
            print("[PASS] Oracle-120 credentials deleted from Windows Credential Manager")
        else:
            return launch(args.once)
    except (OSError, RuntimeError, ValueError) as error:
        # Avoid printing errors containing key material or full RPC URLs.
        print("[HOLD] Credential operation failed (%s)" % type(error).__name__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
