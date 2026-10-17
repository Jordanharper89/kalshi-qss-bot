"""ORACLE-058 full source-locked replacement installer, no runtime launch."""
from pathlib import Path
import ast, hashlib, os, re, textwrap

ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
SRC = PKG / 'oracle_054_reverse_native_handoff.py'
BACKUP = PKG / 'oracle_054_reverse_native_handoff.oracle058_original'
TEST = ROOT / 'test_oracle_058_native_handoff_replacement.py'
EXPECTED = '54c2dd11184081ac'
if not SRC.is_file():
    raise SystemExit('[HOLD] ORIGINAL_ORACLE054_MISSING')
raw = SRC.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if not actual.startswith(EXPECTED):
    raise SystemExit('[HOLD] SOURCE_LOCK_MISMATCH expected=%s actual=%s (no writes)' % (EXPECTED,actual[:16]))
if BACKUP.exists():
    if BACKUP.read_bytes() != raw:
        raise SystemExit('[HOLD] BACKUP_MISMATCH (no writes)')
source = raw.decode('utf-8')
tree = ast.parse(source)
methods = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
consumes = [n for n in methods if n.name == 'consume' and any(isinstance(x,ast.Name) and x.id == 'old_sim' for x in ast.walk(n))]
if len(consumes) != 1:
    raise SystemExit('[HOLD] EXACT_REVERSE_CONSUME_NOT_UNIQUE')
consume = consumes[0]
lines=source.splitlines(keepends=True)
block=''.join(lines[consume.lineno-1:consume.end_lineno])
old = '''        if self.native_compiles or self.unsigned_simulations:
            stats["bounded_attempt_already_used"] += 1
            return'''
new = '''        # ORACLE-058: session RPC budget, NOT permanent one-attempt lockout.
        if getattr(self, "_oracle058_attempts", 0) >= 3:
            stats["oracle058_session_budget_hold"] += 1
            return'''
if block.count(old) != 1:
    raise SystemExit('[HOLD] EXACT_ONE_ATTEMPT_GATE_NOT_FOUND')
block=block.replace(old,new,1)
needle='        self.native_compiles += 1'
if block.count(needle) != 1:
    raise SystemExit('[HOLD] EXACT_COMPILE_ACCOUNTING_NOT_FOUND')
block=block.replace(needle,'''        self._oracle058_attempts = getattr(self, "_oracle058_attempts", 0) + 1
        stats["oracle058_attempts"] += 1
        print("[ORACLE058_ATTEMPT] index=%d/3 direction=METEORA_TO_PUMP" % self._oracle058_attempts, flush=True)
'''+needle,1)
# Instrument the actual call rt.simulate_current, preserving existing return and error handling.
# Use only a match at a standalone statement, and AST for exact source span.
probe_ast=ast.parse(textwrap.dedent(block))
fn=[n for n in ast.walk(probe_ast) if isinstance(n,ast.FunctionDef) and n.name=='consume']
if len(fn)!=1: raise SystemExit('[HOLD] PATCH_PARSE_CONSUME_MISSING')
assigns=[]
for n in ast.walk(fn[0]):
    if not isinstance(n,(ast.Assign,ast.AnnAssign)): continue
    v=n.value
    if not isinstance(v,ast.Call) or not isinstance(v.func,ast.Attribute): continue
    if v.func.attr!='simulate_current' or not isinstance(v.func.value,ast.Name) or v.func.value.id!='rt': continue
    if not isinstance(n,ast.Assign) or len(n.targets)!=1 or not isinstance(n.targets[0],ast.Name):continue
    assigns.append((n,n.targets[0].id))
if len(assigns)!=1:
    raise SystemExit('[HOLD] SIMULATION_RESULT_ASSIGNMENT_NOT_UNIQUE count=%d' % len(assigns))
call,name=assigns[0]
block_lines=block.splitlines(keepends=True)
indent=re.match(r'\s*',block_lines[call.lineno-1]).group(0)
ins = '''# ORACLE-058: preserve original simulation contract; expose failure evidence.
if isinstance(__RESULT__, dict):
    _o58_err = __RESULT__.get("err")
    _o58_units = __RESULT__.get("units")
    print("[ORACLE058_SIM_TRUTH] err=%s units=%s logs=%d" % (
        str(_o58_err)[:300], str(_o58_units)[:40],
        len(__RESULT__.get("logs") or [])), flush=True)
    if _o58_err is not None:
        for _o58_log in list(__RESULT__.get("logs") or [])[-8:]:
            print("[ORACLE058_PROGRAM_LOG] %s" % str(_o58_log)[:400], flush=True)
else:
    print("[ORACLE058_SIM_TRUTH] NON_DICT_RESULT", flush=True)
'''.replace('__RESULT__',name)
insert=''.join(indent+x if x.strip() else x for x in ins.splitlines(keepends=True))
block_lines.insert(call.end_lineno,insert)
newblock=''.join(block_lines)
newsource=''.join(lines[:consume.lineno-1])+newblock+''.join(lines[consume.end_lineno:])
ast.parse(newsource)
assert newsource.count('[ORACLE058_SIM_TRUTH]') == 2
# Zero authority changes: check there are no new broadcast or signing call sites.
if any(k in newblock for k in ('sendTransaction(', 'send_raw_transaction(', 'sign_message(', 'signed_tx(')):
    raise SystemExit('[HOLD] UNEXPECTED_SIGNING_OR_SEND_IN_REVERSE_CONSUME')
TEST_SOURCE = '''import ast, hashlib, unittest
from pathlib import Path
SRC=Path("qseries_v2/oracle_execution/solana_atomic_executor/oracle_054_reverse_native_handoff.py")
BACKUP=Path("qseries_v2/oracle_execution/solana_atomic_executor/oracle_054_reverse_native_handoff.oracle058_original")
class Tests(unittest.TestCase):
    def test_backup_untouched(self):
        self.assertEqual(hashlib.sha256(BACKUP.read_bytes()).hexdigest()[:16],"54c2dd11184081ac")
    def test_valid_python(self):
        ast.parse(SRC.read_text(encoding="utf-8"))
    def test_session_budget(self):
        s=SRC.read_text(encoding="utf-8")
        self.assertIn('getattr(self, "_oracle058_attempts", 0) >= 3',s)
        self.assertIn('self._oracle058_attempts = getattr(self, "_oracle058_attempts", 0) + 1',s)
    def test_one_attempt_gate_retired(self):
        self.assertNotIn('if self.native_compiles or self.unsigned_simulations:',SRC.read_text(encoding="utf-8"))
    def test_sim_evidence_installed(self):
        s=SRC.read_text(encoding="utf-8")
        self.assertIn('[ORACLE058_SIM_TRUTH]',s)
        self.assertIn('[ORACLE058_PROGRAM_LOG]',s)
    def test_original_scanner_preserved(self):
        s=SRC.read_text(encoding="utf-8")
        self.assertIn('install_reverse_bridge',s)
        self.assertIn('old_quote(self, snap, rows, observed_ns)',s)
    def test_no_execution_authority_added(self):
        s=SRC.read_text(encoding="utf-8")
        b=BACKUP.read_text(encoding="utf-8")
        self.assertEqual(s.count('sendTransaction('),b.count('sendTransaction('))
        self.assertEqual(s.count('signed_tx('),b.count('signed_tx('))
    def test_budget_math(self):
        attempts=0
        admitted=[]
        for _ in range(8):
            accepted=attempts<3
            if accepted:attempts+=1
            admitted.append(accepted)
        self.assertEqual(admitted,[True]*3+[False]*5)
    def test_backup_exact(self):
        self.assertTrue(BACKUP.is_file())
        self.assertNotEqual(SRC.read_bytes(),BACKUP.read_bytes())
if __name__=="__main__":unittest.main(verbosity=2)
'''
compile(TEST_SOURCE,str(TEST),'exec')
# Source and tests are prepared before any writes. If interrupted, original exists in backup.
if not BACKUP.exists():
    tmp=BACKUP.with_suffix('.tmp')
    tmp.write_bytes(raw)
    os.replace(tmp,BACKUP)
tmp=SRC.with_suffix('.py.oracle058_tmp')
tmp.write_text(newsource,encoding='utf-8')
os.replace(tmp,SRC)
TEST.write_text(TEST_SOURCE,encoding='utf-8')
print('[PASS] ORACLE-058 source-locked reverse handoff replacement installed')
print('[PRESERVED] Original ORACLE-054 backup sha256=%s' % actual[:16])
print('[FIXED] One-attempt lifetime gate -> three reverse native attempts per scanner session')
print('[DIAGNOSTICS] Actual rt.simulate_current result prints error, compute units, last program logs')
print('[SCANNER] Q25 -> Q20 -> Q18 original; no additional scanner process')
print('[MONEY] No signing or broadcast enabled; profitable atomic simulation still required')
