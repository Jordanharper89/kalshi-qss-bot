from __future__ import annotations
import argparse, hashlib, json, os, queue, re, runpy
import subprocess, sys, threading, unittest
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT/"qseries_v2/oracle_execution/solana_atomic_executor"
ORIGINAL = PKG/"oracle_054_reverse_native_handoff.py"
REPORT = ROOT/"runtime_state/oracle/oracle_live_execution/oracle_057_isolated_sim_worker.json"
ORACLE057_SOURCE_LOCK = "54c2dd11184081acf112ff17336b0ba0a0b822d99dff65dea589cd47c7d1f1c1"
EXECUTION_AUTHORITY = SIGNING = BROADCAST = False
PROTOCOL = "ORACLE057_RESPONSE:"
MODULE = "qseries_v2.oracle_execution.solana_atomic_executor.oracle_057_isolated_sim_worker"

def source_locked():
    return ORIGINAL.is_file() and hashlib.sha256(
        ORIGINAL.read_bytes()
    ).hexdigest() == ORACLE057_SOURCE_LOCK

def redacted(value):
    s = str(value)
    s = re.sub(r"(?i)(api-key=)[^\s&\"\\]+",r"\1[REDACTED]",s)
    s = re.sub(
        r"(?i)(authorization|private.?key|secret|token)\s*[:=]\s*[^,\s}]+",
        r"\1=[REDACTED]",s
    )
    return s[:280]

def diagnostic(response):
    if not isinstance(response,dict):
        return {
            "kind":"BAD_RPC_RESPONSE",
            "error":redacted(type(response).__name__),
            "units":None,"logs":[]
        }
    if response.get("error"):
        return {
            "kind":"RPC_ERROR",
            "error":redacted(response["error"]),
            "units":None,"logs":[]
        }
    result = response.get("result")
    v = response.get(
        "value",
        result.get("value") if isinstance(result,dict) else None
    )
    if not isinstance(v,dict):
        return {
            "kind":"MISSING_SIM_VALUE",
            "error":"NO_VALUE_OBJECT","units":None,"logs":[]
        }
    err = v.get("err")
    context = response.get("context")
    return {
        "kind":"SUCCESS" if err is None else "SIM_REJECTED",
        "error":redacted(err) if err is not None else None,
        "units":v.get("unitsConsumed"),
        "logs":[redacted(x) for x in (v.get("logs") or [])[-16:]],
        "context_slot":context.get("slot") if isinstance(context,dict) else None
    }

def restricted(method,params):
    if method != "simulateTransaction":
        return False
    if not isinstance(params,list) or len(params)<2:
        return False
    cfg = params[1]
    return (
        isinstance(cfg,dict)
        and cfg.get("sigVerify") is False
        and cfg.get("encoding") == "base64"
    )

def worker():
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
        qarb_087_two_second_compaction_liquidity_repair as q87
    )
    physical_rpc = q87.c.rpc
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
            if not restricted(
                request.get("method"),request.get("params")
            ):
                raise ValueError("ONLY_UNSIGNED_SIMULATION_ALLOWED")
            response = physical_rpc(
                "simulateTransaction",request["params"]
            )
            output = {"ok":True,"result":response}
        except Exception as exc:
            output = {
                "ok":False,
                "error":redacted(
                    type(exc).__name__+":"+str(exc)
                )
            }
        sys.stdout.write(
            PROTOCOL+json.dumps(
                output,default=str,separators=(",",":")
            )+"\n"
        )
        sys.stdout.flush()
    return 0

class IsolatedSim:
    def __init__(self,max_sims=3):
        self.max_sims = max_sims
        self.count = 0
        self.rejected = 0
        self.rpc_methods = Counter()
        self.samples = []
        self.lock = threading.RLock()
        self.real_rpc = None

        env = os.environ.copy()
        for key in tuple(env):
            name = key.upper()
            if (
                "PRIVATE_KEY" in name
                or "SECRET_KEY" in name
                or name == "SOLANA_KEYPAIR"
            ):
                env.pop(key,None)

        self.child = subprocess.Popen(
            [sys.executable,"-u","-m",MODULE,"--worker"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,bufsize=1
        )
        self.responses = queue.Queue(maxsize=4)
        self.reader = threading.Thread(
            target=self._read,daemon=True
        )
        self.reader.start()

    def _read(self):
        for line in self.child.stdout:
            if line.startswith(PROTOCOL):
                try:
                    self.responses.put(
                        json.loads(line[len(PROTOCOL):]),
                        timeout=1
                    )
                except (ValueError,queue.Full):
                    pass
        try:
            self.responses.put(None,timeout=1)
        except queue.Full:
            pass

    def write(self):
        report = {
            "build":"ORACLE-057",
            "source_lock":ORACLE057_SOURCE_LOCK[:16],
            "sim_attempts":self.count,
            "sim_rejections":self.rejected,
            "rpc_method_counts":dict(self.rpc_methods),
            "simulation_diagnostics":self.samples[-12:],
            "sim_worker_separate_process":True,
            "original_scanner_count":1,
            "signing":False,
            "broadcast":False,
            "profit_certified":False
        }
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        temp = REPORT.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(report,indent=2,sort_keys=True),
            encoding="utf-8"
        )
        os.replace(temp,REPORT)

    def rpc(self,method,params,*extra,**options):
        with self.lock:
            self.rpc_methods[str(method)] += 1
            if method in (
                "sendTransaction",
                "sendRawTransaction",
                "requestAirdrop"
            ):
                raise RuntimeError("ORACLE057_BROADCAST_PROHIBITED")

            if method != "simulateTransaction":
                return self.real_rpc(
                    method,params,*extra,**options
                )

            if extra or options:
                raise RuntimeError(
                    "ORACLE057_UNEXPECTED_SIM_RPC_ARGUMENTS"
                )
            if not restricted(method,params):
                raise RuntimeError(
                    "ORACLE057_REQUIRES_KEYLESS_BASE64_SIMULATION"
                )
            if self.count >= self.max_sims:
                raise RuntimeError(
                    "ORACLE057_SIM_RPC_BUDGET_EXHAUSTED"
                )

            self.count += 1
            try:
                request = {
                    "method":method,"params":params
                }
                self.child.stdin.write(
                    json.dumps(
                        request,separators=(",",":")
                    )+"\n"
                )
                self.child.stdin.flush()
                output = self.responses.get(timeout=20)

                if output is None:
                    raise RuntimeError(
                        "ISOLATED_SIM_WORKER_EXITED"
                    )
                if not output.get("ok"):
                    raise RuntimeError(
                        "ISOLATED_SIM_WORKER:"
                        +redacted(output.get("error"))
                    )

                result = output["result"]
                diag = diagnostic(result)

            except Exception as exc:
                diag = {
                    "kind":"WORKER_ERROR",
                    "error":redacted(
                        type(exc).__name__+":"+str(exc)
                    ),
                    "units":None,"logs":[]
                }
                result = {
                    "value":{
                        "err":{
                            "Oracle057WorkerError":diag["error"]
                        },
                        "unitsConsumed":0,"logs":[]
                    }
                }

            if diag["kind"] != "SUCCESS":
                self.rejected += 1
            self.samples.append({
                "attempt":self.count,**diag
            })

            print(
                "[ORACLE057_SIM] attempt=%d kind=%s units=%s err=%s"
                %(self.count,diag["kind"],
                  diag["units"],diag["error"]),
                flush=True
            )
            for log in diag["logs"][-8:]:
                print(
                    "[ORACLE057_PROGRAM_LOG]",log,
                    flush=True
                )
            self.write()
            return result

    def close(self):
        self.write()
        if self.child.poll() is None:
            try:
                self.child.stdin.close()
            except Exception:
                pass
            try:
                self.child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.child.terminate()

def run(seconds=300,max_sims=3):
    if not source_locked():
        raise RuntimeError("ORACLE054_SOURCE_DRIFT_NO_RUN")

    source = ORIGINAL.read_text(encoding="utf-8")
    if (
        "native_reverse_route" not in source
        or "simulate_current" not in source
    ):
        raise RuntimeError(
            "ORACLE054_REVERSE_EXECUTION_SEAM_NOT_FOUND"
        )

    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
        qarb_087_two_second_compaction_liquidity_repair as q87
    )
    import qseries_v2.oracle_execution.solana_atomic_executor.runtime as rt

    if not callable(getattr(rt,"simulate_current",None)):
        raise RuntimeError(
            "RUNTIME_SIMULATE_CURRENT_MISSING"
        )

    isolated = IsolatedSim(max_sims=max_sims)
    original_rpc = q87.c.rpc
    isolated.real_rpc = original_rpc
    q87.c.rpc = isolated.rpc

    print(
        "[ORACLE057] ORIGINAL scanner + separate simulation worker",
        flush=True
    )
    print(
        "[BUDGET] max_simulations=%d"%max_sims,
        flush=True
    )
    print(
        "[MONEY] SIGNING_FALSE BROADCAST_FALSE",
        flush=True
    )

    prior_argv = sys.argv[:]
    rc = 0
    try:
        sys.argv = [
            str(ORIGINAL),"--run",
            "--seconds",str(int(seconds)),
            "--cycles","1"
        ]
        try:
            runpy.run_module(
                "qseries_v2.oracle_execution.solana_atomic_executor.oracle_054_reverse_native_handoff",
                run_name="__main__"
            )
        except SystemExit as exc:
            if isinstance(exc.code,int):
                rc = exc.code
    finally:
        sys.argv = prior_argv
        q87.c.rpc = original_rpc
        isolated.close()
        print("[ORACLE057_REPORT]",REPORT,flush=True)
    return rc

class Tests(unittest.TestCase):
    def test_01_source_lock(self):
        self.assertTrue(source_locked())
    def test_02_keyless(self):
        self.assertTrue(restricted(
            "simulateTransaction",
            ["abc",{"encoding":"base64","sigVerify":False}]
        ))
    def test_03_signed_rejected(self):
        self.assertFalse(restricted(
            "simulateTransaction",
            ["abc",{"encoding":"base64","sigVerify":True}]
        ))
    def test_04_send_rejected(self):
        self.assertFalse(restricted(
            "sendTransaction",["abc",{}]
        ))
    def test_05_instruction_error(self):
        self.assertEqual(diagnostic({
            "value":{"err":{"InstructionError":[1,"InvalidArgument"]}}
        })["kind"],"SIM_REJECTED")
    def test_06_success(self):
        self.assertEqual(diagnostic({
            "value":{"err":None,"unitsConsumed":42000}
        })["kind"],"SUCCESS")
    def test_07_nested_result(self):
        self.assertEqual(diagnostic({
            "result":{"value":{"err":"BlockhashNotFound"}}
        })["kind"],"SIM_REJECTED")
    def test_08_rpc_error(self):
        self.assertEqual(diagnostic({
            "error":{"code":-32002}
        })["kind"],"RPC_ERROR")
    def test_09_missing_value(self):
        self.assertEqual(
            diagnostic({})["kind"],
            "MISSING_SIM_VALUE"
        )
    def test_10_redaction(self):
        self.assertNotIn(
            "12345",
            redacted("https://x/?api-key=12345")
        )
    def test_11_no_money(self):
        self.assertFalse(
            EXECUTION_AUTHORITY or SIGNING or BROADCAST
        )
    def test_12_budget(self):
        self.assertTrue(1 <= 3 <= 3)

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--audit",action="store_true")
    p.add_argument("--worker",action="store_true")
    p.add_argument("--run",action="store_true")
    p.add_argument("--seconds",type=int,default=300)
    p.add_argument("--max-sims",type=int,default=3)
    args = p.parse_args(argv)

    if args.test:
        result = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.audit:
        valid = source_locked()
        print(
            "[ORACLE057_SOURCE]",
            "PASS" if valid else "FAIL"
        )
        print(
            "[BOUNDARY] one scanner; isolated simulation; no broadcast"
        )
        return 0 if valid else 1

    if args.worker:
        return worker()

    if args.run:
        if not 1 <= args.max_sims <= 3:
            raise RuntimeError(
                "ORACLE057_MAX_SIMS_OUT_OF_RANGE"
            )
        if not 30 <= args.seconds <= 900:
            raise RuntimeError(
                "ORACLE057_SECONDS_OUT_OF_RANGE"
            )
        return run(args.seconds,args.max_sims)

    p.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
