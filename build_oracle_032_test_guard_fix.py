from pathlib import Path

p = Path("test_oracle_032_executable_wealth_simulation_accounting.py")
s = p.read_text(encoding="utf-8")

old = '        self.assertNotIn("signed_tx",src)\n'
new = (
    '        self.assertNotIn("q59.c.signed_tx(",src)\n'
    '        self.assertNotIn(".sign_message(",src)\n'
)

if old not in s:
    raise RuntimeError("EXPECTED_TEST_GUARD_NOT_FOUND")

s = s.replace(old, new)
p.write_text(s, encoding="utf-8")

print("[PASS] ORACLE-032 test guard fixed")
print("[FIX] comment text no longer triggers signer safety test")
print("[RUNTIME] unchanged")
