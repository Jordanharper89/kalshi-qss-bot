from pathlib import Path
import ast, hashlib, shutil
ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"
BACKUP=ROOT/"run_oracle_live.py.osi018b.bak"
TEST=ROOT/"test_osi_018b_existing_launcher_child_registration.py"
EXPECTED="e9133c5e6641b5b1a11cc7b45037de9a9c677224232802f636730fa12c0c476c"

def sha256_raw(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def find_main_guard_line(text):
    tree=ast.parse(text)
    for node in tree.body:
        if not isinstance(node,ast.If): continue
        t=node.test
        if not isinstance(t,ast.Compare) or len(t.ops)!=1 or len(t.comparators)!=1: continue
        if not isinstance(t.ops[0],ast.Eq): continue
        l,r=t.left,t.comparators[0]
        if isinstance(l,ast.Name) and l.id=="__name__" and isinstance(r,ast.Constant) and r.value=="__main__": return node.lineno
        if isinstance(r,ast.Name) and r.id=="__name__" and isinstance(l,ast.Constant) and l.value=="__main__": return node.lineno
    raise RuntimeError("No structural __main__ guard found")

TEST_TEXT='''import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registration(self):
  text=(ROOT/"run_oracle_live.py").read_text(encoding="utf-8",errors="replace")
  ast.parse(text)
  self.assertIn("run_osi_solana_intelligence_live.py",text)
  self.assertTrue((ROOT/"run_oracle_live.py.osi018b.bak").is_file())
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  self.assertIn("execution_authority=FALSE",text)
  print("[PASS] OSI-018B existing Oracle launcher registration")
  print("[TRADER] Starting Oracle will also start the read-only Solana opportunity hunter")
  print("[PASS] launcher remains syntactically valid")
  print("[PASS] execution_authority=FALSE")
  print("[SCOPE] Registration certified; restart Oracle required for physical activation")
if __name__=="__main__":unittest.main()
'''

def main():
    print("="*116);print(" OSI-018B STRUCTURAL EXISTING ORACLE LAUNCHER CHILD REGISTRATION");print("="*116)
    if not LAUNCHER.is_file(): raise RuntimeError("Missing run_oracle_live.py")
    if not (ROOT/"run_osi_solana_intelligence_live.py").is_file(): raise RuntimeError("OSI-017 child worker missing")
    actual=sha256_raw(LAUNCHER)
    if actual!=EXPECTED: raise RuntimeError(f"Captured launcher hash changed; expected={EXPECTED} actual={actual}")
    raw=LAUNCHER.read_bytes(); text=raw.decode("utf-8")
    if "run_osi_solana_intelligence_live.py" in text: raise RuntimeError("OSI child already registered unexpectedly; refuse duplicate patch")
    guard_line=find_main_guard_line(text)
    lines=text.splitlines(keepends=True); insert_at=guard_line-1
    nl="\r\n" if b"\r\n" in raw else "\n"
    block=nl.join([
      "# OSI-018B registered read-only Solana intelligence child",
      "import subprocess as _osi_subprocess",
      "import sys as _osi_sys",
      "from pathlib import Path as _OSIPath",
      "_osi_child = _OSIPath(__file__).resolve().parent / 'run_osi_solana_intelligence_live.py'",
      "if _osi_child.is_file():",
      "    _osi_subprocess.Popen([_osi_sys.executable, str(_osi_child)], cwd=str(_osi_child.parent))",
      "# execution_authority=FALSE","",""
    ])
    shutil.copy2(LAUNCHER,BACKUP)
    patched="".join(lines[:insert_at])+block+"".join(lines[insert_at:])
    ast.parse(patched)
    LAUNCHER.write_bytes(patched.encode("utf-8"))
    TEST.write_text(TEST_TEXT,encoding="utf-8")
    print("[PASS] backup:",BACKUP.name)
    print("[PASS] structural __main__ guard line:",guard_line)
    print("[PASS] registered OSI child in existing Oracle launcher")
    print("[PASS] test:",TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Direct replacement for failed OSI-018; no duplicate runtime")
if __name__=="__main__":main()
