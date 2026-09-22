
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

def _sports_is_last_child(source):
    m=re.search(r"CHILDREN\s*=\s*\{(.*?)\n\}",source,re.S)
    if not m:raise RuntimeError("CHILDREN registry not found")
    keys=re.findall(r'["\\\']([^"\\\']+)["\\\']\s*:',m.group(1))
    if not keys or keys[-1]!="sports":
        raise RuntimeError("sports is not final native CHILDREN entry; refusing destructive gate")
    return keys

def run_gate(root=None,timeout=150.0):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    s094=_read(root/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")
    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    if actual!=s094.get("post_patch_sha256"):raise RuntimeError("launcher hash mismatch")
    keys=_sports_is_last_child(launcher.read_text(encoding="utf-8"))

    env=os.environ.copy();env["PYTHONUNBUFFERED"]="1"
    p=subprocess.Popen([sys.executable,str(launcher),"--cadence-seconds","2"],
        cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,bufsize=1,env=env)
    lines=[]
    sports_pid=None
    try:
        # Capture the direct child set on the first Oracle heartbeat while every
        # restart counter is still zero. Native _spawn walks CHILDREN in order,
        # and sports is statically proven to be the final registry entry.
        deadline=time.time()+35
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                if "[ORACLE] heartbeat=1 " in line:
                    if "sports_restarts=0" not in line:
                        raise RuntimeError("sports had already restarted before PID capture")
                    rows=_child_entries(p.pid)
                    timed=[]
                    for pid,exe in rows:
                        t=_creation_ticks(pid)
                        if t is not None:timed.append((t,pid,exe))
                    if len(timed)<len(keys):
                        # give process table a brief moment to settle
                        time.sleep(0.5)
                        timed=[]
                        for pid,exe in _child_entries(p.pid):
                            t=_creation_ticks(pid)
                            if t is not None:timed.append((t,pid,exe))
                    if not timed:raise RuntimeError("no direct Oracle children found")
                    timed.sort()
                    sports_pid=timed[-1][1]
                    break
            if p.poll() is not None:raise RuntimeError("launcher exited before first heartbeat")
        if sports_pid is None:raise RuntimeError("first-heartbeat sports PID capture failed")

        # Do not kill until the exact captured child has been observed under
        # sports=HEALTHY with zero sports restarts.
        deadline=time.time()+80
        ready=False
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                if "sports=HEALTHY" in line and "sports_restarts=0" in line:
                    current={pid for pid,_ in _child_entries(p.pid)}
                    if sports_pid not in current:
                        raise RuntimeError("captured final child exited before controlled restart")
                    ready=True;break
            if p.poll() is not None:raise RuntimeError("launcher exited before controlled sports restart")
        if not ready:raise RuntimeError("sports did not become healthy before controlled restart")

        _terminate(sports_pid)

        restarts=0
        healthy=False
        replacement=None
        deadline=time.time()+timeout
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                m=re.search(r"sports_restarts=(\d+)",line)
                if m:restarts=max(restarts,int(m.group(1)))
                if "sports=HEALTHY" in line and restarts>=1:
                    current=[]
                    for pid,exe in _child_entries(p.pid):
                        t=_creation_ticks(pid)
                        if t is not None:current.append((t,pid,exe))
                    newer=[x for x in current if x[1]!=sports_pid]
                    newer.sort()
                    if newer:replacement=newer[-1][1]
                    healthy=True;break
            if p.poll() is not None:
                raise RuntimeError("production launcher exited after exact sports-child termination")

        if not healthy:raise RuntimeError("sports did not recover HEALTHY after exact child termination")

        result={
            "children_registry_order":keys,
            "sports_was_last_registry_entry":True,
            "sports_pid_before":sports_pid,
            "sports_pid_after":replacement,
            "sports_restarts_after":restarts,
            "sports_healthy_after_restart":True,
            "launcher_alive":p.poll() is None,
            "inspection_method":"WIN32_TOOLHELP32_PLUS_CREATION_TIME",
            "wmic_used":False,
            "powershell_used":False,
            "terminal_dependency":"NONE",
            "execution_authority":False,
        }
        state=root/"qseries_v2/oracle_source_network/state/osn096_native_sports_restart_recovery_gate.json"
        state.write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=20)
            except Exception:p.kill()
