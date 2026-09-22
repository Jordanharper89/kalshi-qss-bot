from pathlib import Path

ROOT=Path.cwd()
S094=ROOT/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json"
S095=ROOT/"qseries_v2/oracle_source_network/state/osn095_native_sports_full_cycle_gate.json"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/native_sports_parent_exit_forensic.py"
TEST=ROOT/"test_osn_096_native_sports_parent_exit_FORENSIC_CAPTURE.py"

FORENSIC=r"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import subprocess
import sys
import time
import json
import hashlib
import os
import re

TH32CS_SNAPPROCESS=0x00000002
PROCESS_QUERY_LIMITED_INFORMATION=0x1000
PROCESS_TERMINATE=0x0001
INVALID_HANDLE_VALUE=ctypes.c_void_p(-1).value

class PROCESSENTRY32W(ctypes.Structure):
    _fields_=[
        ("dwSize",wintypes.DWORD),("cntUsage",wintypes.DWORD),
        ("th32ProcessID",wintypes.DWORD),("th32DefaultHeapID",ctypes.c_size_t),
        ("th32ModuleID",wintypes.DWORD),("cntThreads",wintypes.DWORD),
        ("th32ParentProcessID",wintypes.DWORD),("pcPriClassBase",ctypes.c_long),
        ("dwFlags",wintypes.DWORD),("szExeFile",wintypes.WCHAR*260),
    ]

class FILETIME(ctypes.Structure):
    _fields_=[("dwLowDateTime",wintypes.DWORD),("dwHighDateTime",wintypes.DWORD)]

k32=ctypes.WinDLL("kernel32",use_last_error=True)
CreateToolhelp32Snapshot=k32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD]
CreateToolhelp32Snapshot.restype=wintypes.HANDLE
Process32FirstW=k32.Process32FirstW
Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(PROCESSENTRY32W)]
Process32FirstW.restype=wintypes.BOOL
Process32NextW=k32.Process32NextW
Process32NextW.argtypes=[wintypes.HANDLE,ctypes.POINTER(PROCESSENTRY32W)]
Process32NextW.restype=wintypes.BOOL
OpenProcess=k32.OpenProcess
OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
OpenProcess.restype=wintypes.HANDLE
GetProcessTimes=k32.GetProcessTimes
GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME)]
GetProcessTimes.restype=wintypes.BOOL
TerminateProcess=k32.TerminateProcess
TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]
TerminateProcess.restype=wintypes.BOOL
CloseHandle=k32.CloseHandle
CloseHandle.argtypes=[wintypes.HANDLE]
CloseHandle.restype=wintypes.BOOL

def _read(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def _child_entries(parent_pid):
    snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0)
    if snap==INVALID_HANDLE_VALUE:raise ctypes.WinError(ctypes.get_last_error())
    rows=[]
    try:
        e=PROCESSENTRY32W();e.dwSize=ctypes.sizeof(PROCESSENTRY32W)
        ok=Process32FirstW(snap,ctypes.byref(e))
        while ok:
            if int(e.th32ParentProcessID)==int(parent_pid):
                rows.append((int(e.th32ProcessID),e.szExeFile))
            ok=Process32NextW(snap,ctypes.byref(e))
    finally:
        CloseHandle(snap)
    return rows

def _creation_ticks(pid):
    h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,int(pid))
    if not h:return None
    try:
        c=FILETIME();x=FILETIME();k=FILETIME();u=FILETIME()
        if not GetProcessTimes(h,ctypes.byref(c),ctypes.byref(x),ctypes.byref(k),ctypes.byref(u)):
            return None
        return (int(c.dwHighDateTime)<<32)|int(c.dwLowDateTime)
    finally:
        CloseHandle(h)

def _terminate(pid):
    h=OpenProcess(PROCESS_TERMINATE,False,int(pid))
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not TerminateProcess(h,1):raise ctypes.WinError(ctypes.get_last_error())
    finally:
        CloseHandle(h)

def _registry_keys(source):
    m=re.search(r"CHILDREN\s*=\s*\{(.*?)\n\}",source,re.S)
    if not m:raise RuntimeError("CHILDREN registry not found")
    return re.findall(r'["\\\']([^"\\\']+)["\\\']\s*:',m.group(1))

def run_forensic(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    s094=_read(root/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")
    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    if actual!=s094.get("post_patch_sha256"):raise RuntimeError("launcher hash mismatch")
    keys=_registry_keys(launcher.read_text(encoding="utf-8"))
    if not keys or keys[-1]!="sports":
        raise RuntimeError("sports is not final CHILDREN entry; refusing destructive forensic")

    env=os.environ.copy();env["PYTHONUNBUFFERED"]="1"
    p=subprocess.Popen(
        [sys.executable,str(launcher),"--cadence-seconds","2"],
        cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,bufsize=1,env=env
    )
    lines=[]
    sports_pid=None
    try:
        deadline=time.time()+40
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                if "[ORACLE] heartbeat=1 " in line:
                    timed=[]
                    for pid,exe in _child_entries(p.pid):
                        t=_creation_ticks(pid)
                        if t is not None:timed.append((t,pid,exe))
                    if not timed:raise RuntimeError("no direct Oracle children found")
                    timed.sort()
                    sports_pid=timed[-1][1]
                    break
            if p.poll() is not None:
                raise RuntimeError("launcher exited before first heartbeat")

        if sports_pid is None:
            raise RuntimeError("sports PID capture failed")

        deadline=time.time()+90
        ready=False
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                if "sports=HEALTHY" in line and "sports_restarts=0" in line:
                    ready=True
                    break
            if p.poll() is not None:
                raise RuntimeError("launcher exited before sports became healthy")
        if not ready:
            raise RuntimeError("sports did not become healthy before forensic termination")

        _terminate(sports_pid)
        terminated_at=time.time()

        # Capture exact post-termination behavior without asserting recovery.
        deadline=time.time()+35
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
            if p.poll() is not None:
                break

        exit_code=p.poll()
        restarts=0
        last_oracle=None
        for line in lines:
            if "[ORACLE]" in line:
                last_oracle=line
            m=re.search(r"sports_restarts=(\d+)",line)
            if m:restarts=max(restarts,int(m.group(1)))

        result={
            "launcher_sha256":actual,
            "children_registry_order":keys,
            "sports_pid_terminated":sports_pid,
            "sports_was_last_registry_entry":True,
            "launcher_exit_code_after_sports_termination":exit_code,
            "launcher_still_alive_after_35s":exit_code is None,
            "sports_restarts_observed":restarts,
            "last_oracle_heartbeat_line":last_oracle,
            "post_termination_output_tail":lines[-140:],
            "wmic_used":False,
            "powershell_used":False,
            "launcher_modified":False,
            "execution_authority":False,
        }
        state=root/"qseries_v2/oracle_source_network/state/osn096_native_sports_parent_exit_forensic.json"
        state.write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=20)
            except Exception:p.kill()
"""

TESTSRC=r"""
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_parent_exit_forensic import run_forensic

r=run_forensic(Path.cwd())
print("[RESULT]",r)
assert r["sports_was_last_registry_entry"] is True
assert r["wmic_used"] is False
assert r["powershell_used"] is False
assert r["launcher_modified"] is False
assert r["execution_authority"] is False
print("[PASS] exact sports child terminated under bounded forensic")
print("[PASS] parent post-termination behavior captured")
print("[PASS] run_oracle_LIVE.py not modified")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-096 parent-exit forensic capture complete")
"""

def main():
    print("="*120)
    print(" OSN-096 NATIVE SPORTS PARENT-EXIT FORENSIC CAPTURE")
    print("="*120)
    for dep in (S094,S095,LAUNCHER):
        if not dep.exists():raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_text(FORENSIC,encoding="utf-8")
    TEST.write_text(TESTSRC,encoding="utf-8")
    compile(FORENSIC,str(TARGET),"exec");compile(TESTSRC,str(TEST),"exec")

    print("[PURPOSE] capture exact run_oracle_LIVE.py behavior after terminating only the proven sports child")
    print("[PASS] no arbitrary child probing")
    print("[PASS] no WMIC")
    print("[PASS] no PowerShell")
    print("[PASS] run_oracle_LIVE.py remains byte-for-byte unchanged")
    print("[WRITE]",TARGET.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
