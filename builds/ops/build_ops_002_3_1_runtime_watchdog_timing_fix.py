from pathlib import Path

runtime_path = Path("qseries_v2/ops/qseries_runtime.py")
test_path = Path("test_ops_002_3_runtime_watchdog_integration.py")

runtime = runtime_path.read_text(encoding="utf-8")

runtime = runtime.replace(
'''            self.scheduler.register_job(
                name="ops.watchdog.check",
                interval_seconds=self.watchdog_seconds,
                job_callable=self.watchdog.check_once,
                run_immediately=False,
                metadata={"layer": "OPS", "purpose": "watchdog auto-recovery"},
            )''',
'''            self.scheduler.register_job(
                name="ops.watchdog.check",
                interval_seconds=self.watchdog_seconds,
                job_callable=self.watchdog.check_once,
                run_immediately=True,
                metadata={"layer": "OPS", "purpose": "watchdog auto-recovery"},
            )'''
)

test = test_path.read_text(encoding="utf-8")
test = test.replace(
    "time.sleep(0.95)",
    "runtime.watchdog.check_once()\n\n    time.sleep(0.95)"
)

runtime_path.write_text(runtime, encoding="utf-8")
test_path.write_text(test, encoding="utf-8")

print("========================================")
print(" OPS-002.3.1 INSTALLER")
print(" Runtime Watchdog Timing Fix")
print("========================================")
print("[OK] Patched qseries_v2\\ops\\qseries_runtime.py")
print("[OK] Patched test_ops_002_3_runtime_watchdog_integration.py")
print()
print("[DONE] OPS-002.3.1 installed")
print()
print("Run:")
print("python test_ops_002_3_runtime_watchdog_integration.py")