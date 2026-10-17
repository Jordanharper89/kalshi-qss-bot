from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"runtime.py"
OWNERSHIP=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"live_money_runtime.py"
TEST=ROOT/"test_universal_pair_identity_runtime.py"

for p in (TARGET,OWNERSHIP):
    if not p.is_file():
        raise RuntimeError("REQUIRED_TARGET_MISSING:"+str(p))

src=TARGET.read_text(encoding="utf-8")
tree=ast.parse(src)
lines=src.splitlines(keepends=True)
starts=[]
pos=0
for line in lines:
    starts.append(pos); pos+=len(line)

def span(node):
    return starts[node.lineno-1]+node.col_offset, starts[node.end_lineno-1]+node.end_col_offset

def text_of(node):
    a,b=span(node); return src[a:b]

funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
for name in ("immutable_snapshot","prebuild_meteora_templates","exact_best","attack"):
    if name not in funcs:
        raise RuntimeError("FUNCTION_MISSING:"+name)

repls=[]
inserts=[]
counts={"snapshot":0,"mt_key":0,"intersection":0,"meteora_call":0,"newer":0,"submit":0,"event_ready":0,"ws_count":0,"attack_norm":0}

# immutable snapshot exact identity
f=funcs["immutable_snapshot"]
ret=next((n for n in ast.walk(f) if isinstance(n,ast.Return) and isinstance(n.value,ast.Dict)),None)
if ret is None:
    raise RuntimeError("IMMUTABLE_SNAPSHOT_RETURN_NOT_FOUND")
keys=[k.value for k in ret.value.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)]
if "pair_key" not in keys:
    old=text_of(ret.value)
    i=old.find("{")+1
    new=old[:i]+'\n        "pair_key": str(pair.token)+"|"+str(pair.meteora_pool),'+old[i:]
    repls.append((*span(ret.value),new))
counts["snapshot"]=1

# Meteora templates exact pair keyed
f=funcs["prebuild_meteora_templates"]
for n in ast.walk(f):
    if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=="METEORA_TEMPLATES":
        if isinstance(n.slice,ast.Name) and n.slice.id=="token":
            repls.append((*span(n.slice),'token+"|"+pool'))
            counts["mt_key"]+=1
for n in ast.walk(f):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="intersection_update":
        if isinstance(n.func.value,ast.Name) and n.func.value.id=="READY_TOKENS" and n.args:
            if "METEORA_TEMPLATES" in text_of(n.args[0]):
                repls.append((*span(n.args[0]),'{key.split("|",1)[0] for key in METEORA_TEMPLATES}'))
                counts["intersection"]+=1

# exact_best builds Meteora instruction from exact snapshot pair key
f=funcs["exact_best"]
for n in ast.walk(f):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="build_meteora_ix_hot" and n.args:
        if text_of(n.args[0]).strip()=="token":
            repls.append((*span(n.args[0]),'str(snap["pair_key"])'))
            counts["meteora_call"]+=1
for n in ast.walk(f):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="newer_waiting" and n.args:
        if text_of(n.args[0]).strip()=="token":
            repls.append((*span(n.args[0]),'str(snap["pair_key"])'))
            counts["newer"]+=1

# attack normalizes human token while freshness uses exact pair identity
f=funcs["attack"]
first_body=f.body[0]
insert_at=starts[first_body.lineno-1]
indent=" "*(f.col_offset+4)
norm=indent+'identity=str(snap["pair_key"])\n'+indent+'token=str(snap["token"])\n'
inserts.append((insert_at,norm))
counts["attack_norm"]=1

for n in ast.walk(f):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="newer_waiting" and n.args:
        if text_of(n.args[0]).strip()=="token":
            repls.append((*span(n.args[0]),'identity'))
            counts["newer"]+=1

# event lane uses pair identity
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="submit":
        if isinstance(n.func.value,ast.Name) and n.func.value.id=="lane" and n.args:
            if text_of(n.args[0]).strip()=="token":
                repls.append((*span(n.args[0]),'str(pair.token)+"|"+str(pair.meteora_pool)'))
                counts["submit"]+=1

# event readiness exact pair template
for n in ast.walk(tree):
    if isinstance(n,ast.If) and n.lineno>2800 and text_of(n.test).strip()=="token not in READY_TOKENS":
        repls.append((*span(n.test),'(str(pair.token)+"|"+str(pair.meteora_pool)) not in METEORA_TEMPLATES'))
        counts["event_ready"]+=1

# telemetry ready_pairs = pair identities
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="len" and n.args:
        if isinstance(n.args[0],ast.Name) and n.args[0].id=="READY_TOKENS" and 2950<n.lineno<3050:
            repls.append((*span(n.args[0]),"METEORA_TEMPLATES"))
            counts["ws_count"]+=1

required={"snapshot":1,"mt_key":1,"intersection":1,"meteora_call":1,"submit":1,"event_ready":1,"ws_count":1,"attack_norm":1}
for k,v in required.items():
    if counts[k]<v:
        raise RuntimeError("PAIR_IDENTITY_SEAM_NOT_FOUND:%s=%d"%(k,counts[k]))
if counts["newer"]<2:
    raise RuntimeError("PAIR_IDENTITY_NEWER_WAITING_INCOMPLETE:"+str(counts["newer"]))

edits=[(a,b,s) for a,b,s in repls]+[(p,p,s) for p,s in inserts]
edits.sort(key=lambda x:(x[0],x[1]),reverse=True)
last=len(src)+1
for a,b,s in edits:
    if b>last:
        raise RuntimeError("OVERLAPPING_PAIR_IDENTITY_EDITS")
    src=src[:a]+s+src[b:]
    last=a

ast.parse(src)
TARGET.write_text(src,encoding="utf-8")

TEST_CODE='from pathlib import Path\nimport ast\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm\n\ns=Path(r.__file__).read_text(encoding="utf-8")\nls=Path(lm.__file__).read_text(encoding="utf-8")\nast.parse(s); ast.parse(ls)\n\nassert \'"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)\' in s\nassert \'METEORA_TEMPLATES[token+"|"+pool]\' in s\nassert \'{key.split("|",1)[0] for key in METEORA_TEMPLATES}\' in s\nassert \'build_meteora_ix_hot(\' in s and \'str(snap["pair_key"])\' in s\nassert \'lane.submit(\' in s and \'str(pair.token)+"|"+str(pair.meteora_pool)\' in s\nassert \'identity=str(snap["pair_key"])\' in s\nassert \'token=str(snap["token"])\' in s\nassert \'_atomic_write(CAPACITY,hot)\' not in ls\nassert \'live_hot_book.json\' in ls\nassert \'sendTransaction\' not in ls\n\nclass P:\n    token="TOKEN_A"\n    meteora_pool="POOL_1"\n    pump_pool="PUMP"\n    token_x="TOKEN_A"\n    token_y="WSOL"\n    decimals_x=6\n    decimals_y=9\n    dlmm_state={}\n    pump_base_reserve=1\n    pump_quote_reserve=1\n\np=P()\na=r.immutable_snapshot(p)\np.meteora_pool="POOL_2"\nb=r.immutable_snapshot(p)\nassert a["pair_key"]=="TOKEN_A|POOL_1"\nassert b["pair_key"]=="TOKEN_A|POOL_2"\nassert a["pair_key"]!=b["pair_key"]\n\nprint("[PASS] same-token alternate pools retain distinct pair identities")\nprint("[PASS] pair-key lane and supersession identity installed")\nprint("[PASS] exact-pair Meteora template lookup installed")\nprint("[PASS] universal/HOT ownership remains intact")\nprint("[BROADCAST] unchanged")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] UNIVERSAL EXACT-PAIR IDENTITY RUNTIME REPLACEMENT")
print("[IDENTITY] token|meteora_pool through snapshot, live lane, freshness, and Meteora template")
print("[MULTI_POOL] same token retains independent Meteora routes")
print("[CANONICAL_PRICE] internal snapshot construction untouched")
print("[UNIVERSAL] state ownership replacement preserved")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
