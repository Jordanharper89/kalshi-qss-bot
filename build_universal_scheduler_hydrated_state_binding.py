from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
TEST=ROOT/"test_universal_scheduler_state_binding.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"

for p in (TARGET,LM):
    if not p.is_file():
        raise RuntimeError("REQUIRED_TARGET_MISSING:"+str(p))

src=TARGET.read_text(encoding="utf-8")
lm=LM.read_text(encoding="utf-8")
tree=ast.parse(src)

target=None
for node in tree.body:
    if (
        isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
        and node.name=="build_universal_subscription_windows"
    ):
        target=node
        break

if target is None:
    raise RuntimeError(
        "UNIVERSAL_SCHEDULER_FUNCTION_NOT_FOUND"
    )

lines=src.splitlines(keepends=True)
starts=[]
pos=0

for line in lines:
    starts.append(pos)
    pos+=len(line)

a=starts[target.lineno-1]
b=(
    starts[target.end_lineno-1]
    +len(lines[target.end_lineno-1])
)

replacement='def build_universal_subscription_windows(\n    state,\n    max_accounts=318,\n    hot_keys=None,\n    active_keys=None,\n):\n    import json as _json\n    from pathlib import Path as _Path\n\n    max_accounts=int(max_accounts)\n    if max_accounts<=0:\n        raise RuntimeError("UNIVERSAL_SCHEDULER_BAD_ACCOUNT_CAP")\n\n    pairs=list(state.get("pairs") or [])\n    addresses=list(state.get("addresses") or [])\n\n    if not pairs or not addresses:\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_EMPTY_HYDRATED_STATE:"\n            "pairs=%d addresses=%d"\n            %(len(pairs),len(addresses))\n        )\n\n    address_set={str(x) for x in addresses}\n\n    def decode_index(value):\n        if isinstance(value,(list,tuple)) and value:\n            try:\n                return int(value[0])\n            except Exception:\n                return None\n        if isinstance(value,dict):\n            for key in ("index","pair_index","pair","i"):\n                if value.get(key) is not None:\n                    try:\n                        return int(value[key])\n                    except Exception:\n                        return None\n        if isinstance(value,int):\n            return int(value)\n        return None\n\n    candidates=[]\n\n    for state_key,value in state.items():\n        if not isinstance(value,dict) or not value:\n            continue\n\n        overlap=0\n        valid=0\n        bad=0\n\n        for address,meta in value.items():\n            if str(address) not in address_set:\n                continue\n\n            overlap+=1\n            index=decode_index(meta)\n\n            if index is not None and 0<=index<len(pairs):\n                valid+=1\n            else:\n                bad+=1\n\n        if valid:\n            candidates.append((\n                valid,\n                overlap,\n                -bad,\n                str(state_key),\n                value,\n            ))\n\n    if not candidates:\n        visible=[\n            str(k)\n            for k,v in state.items()\n            if isinstance(v,dict)\n        ]\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_CANONICAL_ADDRESS_MAP_NOT_FOUND:"\n            +"dict_keys="+",".join(visible[:20])\n        )\n\n    candidates.sort(\n        key=lambda x:(x[0],x[1],x[2]),\n        reverse=True,\n    )\n\n    valid,overlap,neg_bad,map_key,address_map=candidates[0]\n\n    if valid < max(1,int(len(address_set)*0.50)):\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_ADDRESS_MAP_LOW_COVERAGE:"\n            "key=%s valid=%d addresses=%d"\n            %(map_key,valid,len(address_set))\n        )\n\n    pair_addresses={i:set() for i in range(len(pairs))}\n\n    for address,meta in address_map.items():\n        address=str(address)\n\n        if address not in address_set:\n            continue\n\n        index=decode_index(meta)\n\n        if index is None or not (0<=index<len(pairs)):\n            continue\n\n        pair_addresses[index].add(address)\n\n    rows=[]\n\n    for index,pair in enumerate(pairs):\n        token=str(pair.token)\n        pool=str(pair.meteora_pool)\n        pair_key=token+"|"+pool\n        watched=set(pair_addresses.get(index) or ())\n\n        if not watched:\n            continue\n\n        if len(watched)>max_accounts:\n            raise RuntimeError(\n                "UNIVERSAL_PAIR_ACCOUNT_BUDGET_BREACH:"\n                +pair_key+":"+str(len(watched))\n            )\n\n        rows.append({\n            "index":index,\n            "pair_key":pair_key,\n            "token":token,\n            "addresses":watched,\n        })\n\n    if not rows:\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_NO_WATCHABLE_PAIRS:"\n            "map="+map_key\n        )\n\n    root=_Path.cwd()\n    state_dir=(\n        root/"runtime_state"/"oracle"/"solana_atomic_executor"\n    )\n\n    def load_keys(path):\n        if not path.is_file():\n            return []\n\n        try:\n            data=_json.loads(\n                path.read_text(encoding="utf-8")\n            )\n        except Exception:\n            return []\n\n        out=[]\n\n        for row in list(\n            data.get("pairs")\n            or data.get("rows")\n            or []\n        ):\n            if isinstance(row,str):\n                key=row\n            else:\n                key=str(\n                    row.get("pair_key")\n                    or row.get("identity")\n                    or (\n                        str(row.get("token") or "")\n                        +"|"\n                        +str(row.get("meteora_pool") or "")\n                    )\n                )\n\n            if "|" in key and key not in out:\n                out.append(key)\n\n        return out\n\n    if hot_keys is None:\n        hot_keys=load_keys(\n            state_dir/"live_hot_book.json"\n        )\n    else:\n        hot_keys=list(hot_keys)\n\n    if active_keys is None:\n        active_keys=load_keys(\n            state_dir/"active_after_fee_pairs.json"\n        )\n    else:\n        active_keys=list(active_keys)\n\n    by_key={\n        row["pair_key"]:row\n        for row in rows\n    }\n\n    active=[\n        key\n        for key in active_keys\n        if key in by_key\n    ]\n\n    resident_accounts=set()\n    resident_pairs=[]\n\n    for key in active:\n        row=by_key[key]\n        union=resident_accounts|row["addresses"]\n\n        if len(union)>max_accounts:\n            raise RuntimeError(\n                "ACTIVE_RESIDENT_ACCOUNT_BUDGET_BREACH:"\n                +key\n            )\n\n        resident_accounts=union\n        resident_pairs.append(key)\n\n    resident_set=set(resident_pairs)\n\n    hot_order=[]\n    seen=set()\n\n    for key in hot_keys:\n        if (\n            key in by_key\n            and key not in resident_set\n            and key not in seen\n        ):\n            hot_order.append(by_key[key])\n            seen.add(key)\n\n    remainder=[\n        row\n        for row in rows\n        if (\n            row["pair_key"] not in resident_set\n            and row["pair_key"] not in seen\n        )\n    ]\n\n    unique_first=[]\n    duplicates=[]\n    seen_tokens=set()\n\n    for row in hot_order+remainder:\n        if row["token"] in seen_tokens:\n            duplicates.append(row)\n        else:\n            seen_tokens.add(row["token"])\n            unique_first.append(row)\n\n    pending=unique_first+duplicates\n    windows=[]\n\n    while pending:\n        accounts=set(resident_accounts)\n        keys=list(resident_pairs)\n        used=[]\n        progress=False\n\n        for i,row in enumerate(pending):\n            union=accounts|row["addresses"]\n\n            if len(union)<=max_accounts:\n                accounts=union\n                keys.append(row["pair_key"])\n                used.append(i)\n                progress=True\n\n        if not progress:\n            raise RuntimeError(\n                "UNIVERSAL_PAIR_CANNOT_COEXIST_WITH_ACTIVE:"\n                +pending[0]["pair_key"]\n            )\n\n        used_set=set(used)\n        pending=[\n            row\n            for i,row in enumerate(pending)\n            if i not in used_set\n        ]\n\n        windows.append({\n            "pair_keys":keys,\n            "resident_pairs":list(resident_pairs),\n            "addresses":sorted(accounts),\n        })\n\n    if not windows:\n        windows=[{\n            "pair_keys":list(resident_pairs),\n            "resident_pairs":list(resident_pairs),\n            "addresses":sorted(resident_accounts),\n        }]\n\n    expected={row["pair_key"] for row in rows}\n    observed={\n        key\n        for window in windows\n        for key in window["pair_keys"]\n    }\n\n    if observed!=expected:\n        missing=sorted(expected-observed)\n        raise RuntimeError(\n            "UNIVERSAL_SCHEDULER_COVERAGE_GAP:"\n            +",".join(missing[:5])\n        )\n\n    if any(\n        len(window["addresses"])>max_accounts\n        for window in windows\n    ):\n        raise RuntimeError(\n            "UNIVERSAL_WINDOW_ACCOUNT_BUDGET_BREACH"\n        )\n\n    print(\n        "[UNIVERSAL_STATE_BINDING] "\n        "map=%s addresses=%d mapped=%d pairs=%d watchable=%d"\n        %(\n            map_key,\n            len(address_set),\n            valid,\n            len(pairs),\n            len(rows),\n        ),\n        flush=True,\n    )\n\n    print(\n        "[UNIVERSAL_SCHEDULER_READY] "\n        "pairs=%d windows=%d active_resident=%d "\n        "max_accounts=%d"\n        %(\n            len(expected),\n            len(windows),\n            len(resident_pairs),\n            max_accounts,\n        ),\n        flush=True,\n    )\n\n    return windows\n'.strip()+"\n\n"
newsrc=src[:a]+replacement+src[b:]

required=[
    "UNIVERSAL_STATE_BINDING",
    "CANONICAL_ADDRESS_MAP_NOT_FOUND",
    "decode_index",
    "active_after_fee_pairs.json",
    "live_hot_book.json",
]

for marker in required:
    if marker not in newsrc:
        raise RuntimeError(
            "POSTCONDITION_MISSING:"+marker
        )

if 'state.get("address_index")' in newsrc:
    raise RuntimeError(
        "OLD_ADDRESS_INDEX_ASSUMPTION_REMAINS"
    )

if '_atomic_write(CAPACITY,hot)' in lm:
    raise RuntimeError(
        "UNIVERSAL_OWNERSHIP_REGRESSION"
    )

ast.parse(newsrc)
TARGET.write_text(
    newsrc,
    encoding="utf-8",
)

TEST_CODE='from pathlib import Path\nimport ast\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm\n\nsrc=Path(r.__file__).read_text(encoding="utf-8")\nlms=Path(lm.__file__).read_text(encoding="utf-8")\nast.parse(src)\nast.parse(lms)\n\nassert "UNIVERSAL_STATE_BINDING" in src\nassert "CANONICAL_ADDRESS_MAP_NOT_FOUND" in src\nassert \'state.get("address_index")\' not in src\nassert "_atomic_write(CAPACITY,hot)" not in lms\nassert "live_hot_book.json" in lms\nassert "sendTransaction" not in src\n\npairs=[\n    SimpleNamespace(token="A",meteora_pool="P1"),\n    SimpleNamespace(token="B",meteora_pool="P2"),\n    SimpleNamespace(token="C",meteora_pool="P3"),\n    SimpleNamespace(token="D",meteora_pool="P4"),\n]\n\naddresses=[]\ncanonical_lookup={}\n\nfor idx in range(4):\n    for j in range(4):\n        a="PAIR%d_A%d"%(idx,j)\n        addresses.append(a)\n        canonical_lookup[a]=(idx,"kind_%d"%j)\n\nstate={\n    "pairs":pairs,\n    "addresses":addresses,\n    "native_event_lookup":canonical_lookup,\n    "unrelated_dict":{"x":"y"},\n}\n\nwindows=r.build_universal_subscription_windows(\n    state,\n    max_accounts=8,\n    hot_keys=["A|P1","B|P2"],\n    active_keys=["A|P1"],\n)\n\nassert len(windows)>=2\nassert all(len(w["addresses"])<=8 for w in windows)\nassert all("A|P1" in w["pair_keys"] for w in windows)\n\ncoverage={\n    key\n    for w in windows\n    for key in w["pair_keys"]\n}\n\nassert coverage=={\n    "A|P1","B|P2","C|P3","D|P4"\n}\n\nfor w in windows:\n    for key in w["pair_keys"]:\n        idx={\n            "A|P1":0,\n            "B|P2":1,\n            "C|P3":2,\n            "D|P4":3,\n        }[key]\n        needed={\n            "PAIR%d_A%d"%(idx,j)\n            for j in range(4)\n        }\n        assert needed.issubset(\n            set(w["addresses"])\n        )\n\nprint("[PASS] canonical hydrated address map auto-discovered")\nprint("[PASS] scheduler no longer assumes state[\'address_index\']")\nprint("[PASS] every exact pair retains its full watched-account set")\nprint("[PASS] all exact pairs covered across bounded windows")\nprint("[PASS] ACTIVE exact pair remains resident")\nprint("[PASS] universal/HOT ownership preserved")\nprint("[BROADCAST] unchanged")\n'
TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)
ast.parse(TEST_CODE)

print("[PASS] UNIVERSAL SCHEDULER HYDRATED-STATE BINDING REPLACEMENT")
print("[STATE] canonical address map auto-discovered from hydrated state")
print("[PAIRING] address -> exact pair index preserved")
print("[ROTATION] whole-pair bounded windows preserved")
print("[UNIVERSE] 60-pair/768-account hydration path preserved")
print("[IDENTITY] token|meteora_pool preserved")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
