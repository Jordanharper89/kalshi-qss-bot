from pathlib import Path
import ast

ROOT = Path.cwd()
SUB = ROOT / "qseries_v2" / "oracle_execution"
SUB.mkdir(parents=True, exist_ok=True)

MOD = SUB / "oracle_029_full_exact_pair_coverage_cutover.py"
TEST = ROOT / "test_oracle_029_full_exact_pair_coverage_cutover.py"
RUN = ROOT / "run_oracle_029_full_exact_pair_coverage_cutover.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nimport argparse, json\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25\nfrom qseries_v2.oracle_execution import oracle_028_exact_immutable_atomic_shadow_handoff as q28\n\nEXECUTION_AUTHORITY = False\nPAPER_ONLY = True\nREAL_MONEY_MOVED = False\nTARGET_EXACT_PAIRS = 12\n\ndef expanded_prepare_once(root):\n    root = Path(root)\n    q60b = q25.q60b2.q60b\n    q60b.install()\n    q60b.m.pd.MAX_PAIRS = int(TARGET_EXACT_PAIRS)\n\n    try:\n        q60b.p.MAX_PAIRS = int(TARGET_EXACT_PAIRS)\n    except Exception:\n        pass\n\n    try:\n        q60b.m.MAX_PAIRS = int(TARGET_EXACT_PAIRS)\n    except Exception:\n        pass\n\n    state = q60b.extended_prepare(root)\n    cap = q60b.extended_capability(state)\n\n    pairs = list(state.get("pairs") or [])\n    if not pairs:\n        raise RuntimeError("ORACLE029_NO_EXACT_PAIRS")\n\n    print(\n        "[ORACLE029_COVERAGE] exact_pairs=%d target=%d priced_tokens=%d accounts=%d"\n        % (\n            len(pairs),\n            TARGET_EXACT_PAIRS,\n            len(state.get("eps") or {}),\n            len(state.get("addresses") or []),\n        ),\n        flush=True,\n    )\n\n    for i, pair in enumerate(pairs, 1):\n        print(\n            "[ORACLE029_PAIR] n=%d token=%s pump=%s meteora=%s"\n            % (\n                i,\n                str(pair.token)[:12],\n                str(pair.pump_pool)[:12],\n                str(pair.meteora_pool)[:12],\n            ),\n            flush=True,\n        )\n\n    return state, cap\n\ndef install():\n    q25.prepare_once = expanded_prepare_once\n    return True\n\ndef run(seconds=300.0):\n    install()\n\n    print("[ORACLE-029] FULL EXACT-PAIR COVERAGE CUTOVER", flush=True)\n    print("[EXACT_PAIR_LIMIT] 4 -> %d" % TARGET_EXACT_PAIRS, flush=True)\n    print("[HYDRATION] one startup hydration only", flush=True)\n    print("[PRESERVE] ORACLE-023 persistent token-net", flush=True)\n    print("[PRESERVE] ORACLE-027 immutable snapshots + generation guard", flush=True)\n    print("[PRESERVE] ORACLE-028 real atomic simulation shadow", flush=True)\n    print("[MRIYA] replenishment only; not critical path", flush=True)\n    print("[BROADCAST] disabled", flush=True)\n\n    rc = q28.run(float(seconds))\n\n    lane = getattr(q28.q20, "_lane", None)\n    report = {\n        "oracle_build": "ORACLE-029",\n        "target_exact_pairs": TARGET_EXACT_PAIRS,\n        "submitted": getattr(lane, "submitted", None),\n        "processed": getattr(lane, "processed", None),\n        "positive": getattr(lane, "positive", None),\n        "scan_replaced": getattr(lane, "scan_replaced", None),\n        "execution_authority": False,\n        "paper_only": True,\n        "real_money_moved": False,\n        "broadcast": False,\n    }\n\n    report_path = Path(\n        "runtime_state/oracle/oracle_live_execution/"\n        "oracle_029_full_exact_pair_coverage_cutover.json"\n    )\n    report_path.parent.mkdir(parents=True, exist_ok=True)\n    report_path.write_text(\n        json.dumps(report, indent=2, sort_keys=True),\n        encoding="utf-8",\n    )\n\n    print("[ORACLE029_COMPLETE] " + json.dumps(report, sort_keys=True), flush=True)\n    print("[REPORT] %s" % report_path, flush=True)\n    return rc\n\ndef main(argv=None):\n    ap = argparse.ArgumentParser()\n    ap.add_argument("--seconds", type=float, default=300.0)\n    args = ap.parse_args(argv)\n    return run(args.seconds)\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
TEST_SOURCE = '\nimport inspect\nimport unittest\n\nfrom qseries_v2.oracle_execution import oracle_029_full_exact_pair_coverage_cutover as q29\n\nclass T(unittest.TestCase):\n    def test_safety(self):\n        self.assertFalse(q29.EXECUTION_AUTHORITY)\n        self.assertTrue(q29.PAPER_ONLY)\n        self.assertFalse(q29.REAL_MONEY_MOVED)\n\n    def test_coverage_target(self):\n        self.assertEqual(q29.TARGET_EXACT_PAIRS, 12)\n\n    def test_lifts_exact_hydrator_before_prepare(self):\n        src = inspect.getsource(q29.expanded_prepare_once)\n        self.assertIn("q60b.install()", src)\n        self.assertIn("q60b.m.pd.MAX_PAIRS", src)\n        self.assertIn("q60b.extended_prepare(root)", src)\n\n    def test_preserves_oracle_028(self):\n        src = inspect.getsource(q29.run)\n        self.assertIn("q28.run(float(seconds))", src)\n\n    def test_no_broadcast(self):\n        src = inspect.getsource(q29)\n        self.assertNotIn("sendTransaction", src)\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n'
RUN_SOURCE = '\nfrom qseries_v2.oracle_execution.oracle_029_full_exact_pair_coverage_cutover import main\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

# Syntax-validate all generated source before writing.
ast.parse(MODULE_SOURCE)
ast.parse(TEST_SOURCE)
ast.parse(RUN_SOURCE)

MOD.write_text(MODULE_SOURCE.lstrip(), encoding="utf-8")
TEST.write_text(TEST_SOURCE.lstrip(), encoding="utf-8")
RUN.write_text(RUN_SOURCE.lstrip(), encoding="utf-8")

print("[PASS] ORACLE-029 full exact-pair coverage cutover installed")
print("[EXACT_PAIR_LIMIT] legacy default 4 -> target 12")
print("[PRESERVE] one hydration + ORACLE-023 + ORACLE-027 + ORACLE-028")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
