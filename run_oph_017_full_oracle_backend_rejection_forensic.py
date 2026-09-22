
from __future__ import annotations
import ast,subprocess,sys
from pathlib import Path
ROOT=Path.cwd().resolve();PROD=ROOT/"run_oracle_LIVE.py";TEMP=ROOT/"run_oracle_LIVE_OPH017_FORENSIC.py";FORENSIC=ROOT/"run_oph_017_forensic_canonical_writer.py"
def patch(source):
    tree=ast.parse(source);node=None
    for i in ast.walk(tree):
        if isinstance(i,ast.Assign) and isinstance(i.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in i.targets):node=i.value;break
    if node is None:raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="canonical_writer" and isinstance(v,ast.Constant) and isinstance(v.value,str):
            old=v.value;idx=v.lineno-1
            for tok in (repr(old),'"'+old+'"',"'"+old+"'"):
                if tok in lines[idx]:
                    lines[idx]=lines[idx].replace(tok,repr(FORENSIC.name),1);out="".join(lines);ast.parse(out);return out,old
    raise RuntimeError("canonical_writer child not found")
def main():
    print("="*108);print(" OPH-017 FULL ORACLE BACKEND REJECTION FORENSIC");print("="*108)
    source=PROD.read_text(encoding="utf-8");out,old=patch(source);TEMP.write_text(out,encoding="utf-8",newline="\n")
    print(f"[PRODUCTION WRITER] {old}");print(f"[DIAGNOSTIC WRITER] {FORENSIC.name}");print("[ACTION] Run until [OPH-017 FORENSIC], then Ctrl+C.")
    try:return subprocess.run([sys.executable,str(TEMP)],cwd=str(ROOT)).returncode
    except KeyboardInterrupt:return 0
if __name__=="__main__":raise SystemExit(main())
