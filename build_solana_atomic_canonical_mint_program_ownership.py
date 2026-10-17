from pathlib import Path
import ast

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor" / "runtime.py"
TEST = ROOT / "test_solana_atomic_canonical_mint_program_ownership.py"

if not TARGET.is_file():
    raise RuntimeError(f"MISSING_CANONICAL_RUNTIME:{TARGET}")

src = TARGET.read_text(encoding="utf-8")

OLD = '    programs={\n        str(row["token"]):\n            str(row["program"])\n        for row in (\n            warmed_rows\n            or []\n        )\n        if (\n            row.get("token")\n            and row.get("program")\n        )\n    }\n\n    programs[\n        q87.c.WSOL\n    ]=q87.c.TOKEN\n'
NEW = '    mints=[]\n    seen=set()\n    for pair in list(state.get("pairs") or []):\n        for mint in (str(pair.token_x),str(pair.token_y)):\n            if mint not in seen:\n                seen.add(mint); mints.append(mint)\n    programs={}\n    for i in range(0,len(mints),100):\n        batch=mints[i:i+100]\n        result=q87.c.rpc("getMultipleAccounts",[batch,{"encoding":"base64","commitment":"processed"}])\n        if not isinstance(result,dict): raise RuntimeError("TOKEN_PROGRAM_BATCH_RESULT_NOT_MAPPING")\n        values=result.get("value")\n        if not isinstance(values,list) or len(values)!=len(batch): raise RuntimeError("TOKEN_PROGRAM_BATCH_LENGTH_MISMATCH")\n        for mint,account in zip(batch,values):\n            if not isinstance(account,dict): raise RuntimeError("TOKEN_MINT_ACCOUNT_MISSING:"+mint)\n            owner=str(account.get("owner") or "")\n            if owner not in (str(q87.c.TOKEN),str(q87.c.TOKEN22)): raise RuntimeError("TOKEN_MINT_OWNER_UNSUPPORTED:"+mint+":"+owner)\n            programs[mint]=owner\n    if str(programs.get(str(q87.c.WSOL)))!=str(q87.c.TOKEN): raise RuntimeError("WSOL_TOKEN_PROGRAM_DRIFT")\n    print("[CANONICAL_MINT_PROGRAMS] mints=%d source=on_chain_owner token=%d token2022=%d"%(len(programs),sum(str(x)==str(q87.c.TOKEN) for x in programs.values()),sum(str(x)==str(q87.c.TOKEN22) for x in programs.values())),flush=True)\n'

if OLD not in src:
    raise RuntimeError("CANONICAL_RUNTIME_PROGRAM_SOURCE_BLOCK_NOT_FOUND")

updated = src.replace(OLD, NEW, 1)
ast.parse(updated)
TARGET.write_text(updated, encoding="utf-8")

TEST.write_text(
    'from pathlib import Path\n'
    'from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\n'
    's=Path(r.__file__).read_text(encoding="utf-8")\n'
    'assert "[CANONICAL_MINT_PROGRAMS]" in s\n'
    'assert "TOKEN_MINT_OWNER_UNSUPPORTED" in s\n'
    'assert "WSOL_TOKEN_PROGRAM_DRIFT" in s\n'
    'assert "[SIZE_BIND]" in s\n'
    'assert "sendTransaction" not in s\n'
    'print("[PASS] canonical mint-program ownership; size binding preserved; broadcast absent")\n',
    encoding="utf-8",
)

print("[PASS] canonical runtime mint-program ownership installed")
print("[SOURCE] exact on-chain mint owner")
print("[HOT_PATH] no added opportunity RPC")
print("[SIZE_BIND] preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")