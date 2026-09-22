from pathlib import Path
import ast, json, hashlib

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn091_run_oracle_live_supervision_structure.json"
TEST=ROOT/"test_osn_091_run_oracle_live_exact_supervision_structure_audit.py"

TEST_SOURCE='from pathlib import Path\nimport json,hashlib\n\nroot=Path.cwd()\nstate=json.loads((root/"qseries_v2/oracle_source_network/state/osn091_run_oracle_live_supervision_structure.json").read_text())\np=root/state["launcher_path"]\n\nassert p.exists()\nassert hashlib.sha256(p.read_bytes()).hexdigest()==state["launcher_sha256"]\nassert state["audit_only"] is True\nassert state["launcher_modified"] is False\nassert len(state["main_guards"])>=1\nassert state["execution_authority"] is False\n\nprint("[SHA256]",state["launcher_sha256"])\nprint("[MAIN_NAMED_FUNCTIONS]",state["main_named_functions"])\nprint("[MAIN_GUARDS]",state["main_guards"])\nprint("[SUBPROCESS_CALLS]",state["subprocess_calls"][:20])\nprint("[THREAD_CALLS]",state["thread_calls"][:20])\nprint("[PROCESS_CALLS]",state["process_calls"][:20])\nprint("[RUNTIME_MARKERS]",state["runtime_markers"])\nprint("[SPORTS_CURRENTLY_INTEGRATED]",state["sports_currently_integrated"])\nprint("[PASS] run_oracle_LIVE.py structure audited without modification")\nprint("[PASS] OSN-091 exact supervision structure audit certified")\n'

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    print("="*120)
    print(" OSN-091 RUN_ORACLE_LIVE EXACT SUPERVISION STRUCTURE AUDIT")
    print("="*120)

    if not LAUNCHER.exists():
        raise SystemExit("[FAIL] missing production launcher: run_oracle_LIVE.py")

    source=LAUNCHER.read_text(encoding="utf-8",errors="strict")
    tree=ast.parse(source,filename=str(LAUNCHER))
    lines=source.splitlines()

    functions=[]
    classes=[]
    main_guards=[]
    subprocess_calls=[]
    thread_calls=[]
    process_calls=[]
    runtime_markers={}

    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            functions.append({
                "name":node.name,
                "lineno":node.lineno,
                "end_lineno":getattr(node,"end_lineno",None),
                "async":isinstance(node,ast.AsyncFunctionDef)
            })
        elif isinstance(node,ast.ClassDef):
            classes.append({
                "name":node.name,
                "lineno":node.lineno,
                "end_lineno":getattr(node,"end_lineno",None)
            })
        elif isinstance(node,ast.If):
            try:
                test=ast.unparse(node.test)
            except Exception:
                test=""
            if "__name__" in test and "__main__" in test:
                body=[]
                for stmt in node.body:
                    try:
                        body.append(ast.unparse(stmt))
                    except Exception:
                        body.append(type(stmt).__name__)
                main_guards.append({
                    "lineno":node.lineno,
                    "end_lineno":getattr(node,"end_lineno",None),
                    "test":test,
                    "body":body
                })
        elif isinstance(node,ast.Call):
            try:
                call=ast.unparse(node.func)
            except Exception:
                call=""
            low=call.lower()
            rec={"call":call,"lineno":getattr(node,"lineno",None)}
            if "subprocess" in low or call.endswith("Popen"):
                subprocess_calls.append(rec)
            if "thread" in low:
                thread_calls.append(rec)
            if "process" in low or "multiprocessing" in low:
                process_calls.append(rec)

    for marker in (
        "fast_lane","inventory","reasoning","learning","coverage",
        "canonical_writer","continuity","recovery","crypto_learning",
        "gmgn_intelligence","terminal_dependency","execution_authority"
    ):
        hits=[i+1 for i,line in enumerate(lines) if marker in line.lower()]
        if hits:
            runtime_markers[marker]=hits[:20]

    imports=[]
    for node in tree.body:
        if isinstance(node,ast.Import):
            for x in node.names:
                imports.append(x.name)
        elif isinstance(node,ast.ImportFrom):
            imports.append(node.module or "")

    main_named=[f for f in functions if f["name"].lower() in ("main","run","start","launch","supervise","run_forever")]

    state={
        "launcher_path":"run_oracle_LIVE.py",
        "launcher_sha256":sha256(LAUNCHER),
        "line_count":len(lines),
        "functions":functions,
        "classes":classes,
        "main_named_functions":main_named,
        "main_guards":main_guards,
        "subprocess_calls":subprocess_calls,
        "thread_calls":thread_calls,
        "process_calls":process_calls,
        "runtime_markers":runtime_markers,
        "imports":imports,
        "sports_currently_integrated":(
            "oracle_source_network" in source
            or "sports_supervised_child" in source
            or "osn_sports" in source.lower()
        ),
        "audit_only":True,
        "launcher_modified":False,
        "execution_authority":False
    }

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[LAUNCHER]",LAUNCHER.name)
    print("[SHA256]",state["launcher_sha256"])
    print("[FUNCTIONS]",len(functions))
    print("[MAIN_NAMED_FUNCTIONS]",main_named)
    print("[MAIN_GUARDS]",main_guards)
    print("[SUBPROCESS_CALLS]",subprocess_calls[:20])
    print("[THREAD_CALLS]",thread_calls[:20])
    print("[PROCESS_CALLS]",process_calls[:20])
    print("[RUNTIME_MARKERS]",runtime_markers)
    print("[SPORTS_CURRENTLY_INTEGRATED]",state["sports_currently_integrated"])
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] AUDIT ONLY — run_oracle_LIVE.py not modified")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
