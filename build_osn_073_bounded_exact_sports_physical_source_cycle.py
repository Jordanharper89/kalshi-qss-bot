from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-073 BOUNDED EXACT SPORTS PHYSICAL SOURCE CYCLE INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/certification/exact_sports_physical_source_bindings.py',)
FILES = {'qseries_v2/oracle_source_network/certification/exact_sports_physical_source_cycle.py': 'from dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess\nimport sys\nimport time\n\nfrom qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import BINDINGS\n\n@dataclass(frozen=True)\nclass SourceCycleRow:\n    league: str\n    passed: bool\n    returncode: int\n    elapsed_seconds: float\n    event_lines: int\n    physical_lines: int\n    execution_authority: bool = False\n\ndef run_source_cycle(root=None, per_source_timeout=35):\n    base = Path(root or Path.cwd()).resolve()\n    rows = []\n\n    for binding in BINDINGS:\n        path = base / binding.test_file\n        started = time.monotonic()\n        try:\n            p = subprocess.run(\n                [sys.executable, str(path)],\n                cwd=str(base),\n                text=True,\n                capture_output=True,\n                timeout=float(per_source_timeout),\n            )\n            stdout = p.stdout or ""\n            stderr = p.stderr or ""\n            if stdout:\n                print(stdout, end="" if stdout.endswith("\\n") else "\\n")\n            if stderr:\n                print(stderr, end="" if stderr.endswith("\\n") else "\\n")\n            passed = p.returncode == 0\n            rc = p.returncode\n        except subprocess.TimeoutExpired:\n            stdout = ""\n            passed = False\n            rc = 124\n\n        elapsed = round(time.monotonic() - started, 3)\n        event_lines = sum(1 for line in stdout.splitlines() if line.startswith("[EVENT]"))\n        physical_lines = sum(1 for line in stdout.splitlines() if line.startswith("[PHYSICAL]"))\n        row = SourceCycleRow(binding.league, passed, rc, elapsed, event_lines, physical_lines)\n        print("[SOURCE_CYCLE]", row)\n        rows.append(row)\n\n    return tuple(rows)\n', 'test_osn_073_bounded_exact_sports_physical_source_cycle.py': 'from qseries_v2.oracle_source_network.certification.exact_sports_physical_source_cycle import run_source_cycle\n\nrows = run_source_cycle(per_source_timeout=35)\nassert tuple(r.league for r in rows) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert all(r.passed for r in rows), rows\nassert all(r.execution_authority is False for r in rows)\nassert all((r.event_lines + r.physical_lines) >= 1 for r in rows), rows\n\nprint("[PASS] six admitted sports sources physically executed under hard timeout")\nprint("[PASS] each source produced physical/extraction evidence")\nprint("[PASS] no held or blocked league executed")\nprint("[PASS] OSN-073 bounded physical source cycle certified")\n'}

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + rel)
    print("[PASS] dependency verified:", rel)
    return p

def write_compile(rel, source):
    compile(source, rel, "exec")
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding="utf-8")
    compile(p.read_text(encoding="utf-8"), str(p), "exec")
    print("[WRITE]", rel)
    print("[PASS] post-write compile verified:", rel)

def main():
    print("=" * 120)
    print(" " + TITLE)
    print("=" * 120)
    for rel in REQUIRED:
        require(rel)
    for rel, source in FILES.items():
        write_compile(rel, source)
    print("[PASS] installer completed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
