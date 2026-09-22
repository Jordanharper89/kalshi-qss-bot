
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-265"
REVISION="OAD_265_SOLANA_TOKEN_HOLDER_CONCENTRATION_RATE_LIMIT_RESILIENT_FOUNDATIONAL_REBUILD_V1"
MODULE_NAME='oad_265_solana_token_holder_concentration_intelligence.py'
TEST_NAME='test_oad_265_solana_token_holder_concentration_intelligence.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nimport json, os, time, urllib.error, urllib.request\nfrom decimal import Decimal\nfrom .oad_264_solana_token_mint_authority_supply_intelligence import acquire_solana_token_mint_state\nfrom .oad_252_crypto_independent_source_expansion_foundation import (\n    build_independent_crypto_observation,\n    verify_independent_crypto_observation,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nDEFAULT_RPC="https://api.mainnet.solana.com"\n\ndef _rpc_url():\n    return str(os.getenv("SOLANA_RPC_URL") or DEFAULT_RPC).strip()\n\ndef _retry_after_seconds(exc, attempt):\n    try:\n        value=exc.headers.get("Retry-After")\n        if value is not None:\n            return max(1.0, min(float(value), 20.0))\n    except Exception:\n        pass\n    return min(2.0 ** attempt, 12.0)\n\ndef _rpc(method, params, timeout=20.0, max_attempts=5, sleep_fn=time.sleep):\n    url=_rpc_url()\n    last_error=None\n    for attempt in range(1, int(max_attempts)+1):\n        body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()\n        req=urllib.request.Request(\n            url,\n            data=body,\n            headers={\n                "Content-Type":"application/json",\n                "Accept":"application/json",\n                "User-Agent":"Oracle-Q-Series/1.0",\n            },\n        )\n        try:\n            with urllib.request.urlopen(req,timeout=float(timeout)) as r:\n                d=json.loads(r.read().decode())\n            if d.get("error"):\n                err=d["error"]\n                code=err.get("code") if isinstance(err,dict) else None\n                if code in (-32005,-32004,-32002) and attempt < int(max_attempts):\n                    sleep_fn(min(2.0 ** attempt,12.0))\n                    continue\n                raise RuntimeError("Solana RPC error: "+str(err))\n            return d.get("result")\n        except urllib.error.HTTPError as exc:\n            last_error=exc\n            if exc.code==429 and attempt < int(max_attempts):\n                delay=_retry_after_seconds(exc,attempt)\n                print(f"[RATE_LIMIT] HTTP 429 attempt={attempt}/{max_attempts} retry_after_seconds={delay}")\n                sleep_fn(delay)\n                continue\n            raise\n        except (urllib.error.URLError, TimeoutError) as exc:\n            last_error=exc\n            if attempt < int(max_attempts):\n                delay=min(2.0 ** attempt,12.0)\n                print(f"[RETRY] {type(exc).__name__} attempt={attempt}/{max_attempts} retry_after_seconds={delay}")\n                sleep_fn(delay)\n                continue\n            raise\n    if last_error is not None:\n        raise last_error\n    raise RuntimeError("Solana RPC exhausted without result")\n\ndef acquire_solana_holder_concentration(\n    token_address=None,\n    timeout_seconds=20.0,\n    rpc=_rpc,\n    inter_request_delay_seconds=1.25,\n    sleep_fn=time.sleep,\n):\n    mint=acquire_solana_token_mint_state(token_address,timeout_seconds)\n    token_address=mint.payload["token_address"]\n    supply=Decimal(str(mint.payload["supply_raw"]))\n    if supply <= 0:\n        raise RuntimeError("token supply is not positive")\n\n    if inter_request_delay_seconds > 0:\n        sleep_fn(float(inter_request_delay_seconds))\n\n    res=rpc(\n        "getTokenLargestAccounts",\n        [token_address,{"commitment":"finalized"}],\n        timeout_seconds,\n    )\n    rows=(res or {}).get("value") or []\n    if not rows:\n        raise RuntimeError("largest-account concentration unavailable")\n\n    amounts=[Decimal(str(x.get("amount") or "0")) for x in rows]\n    top1=amounts[0]\n    top5=sum(amounts[:5],Decimal(0))\n    top20=sum(amounts[:20],Decimal(0))\n\n    payload={\n        "token_address":token_address,\n        "slot":(res or {}).get("context",{}).get("slot"),\n        "supply_raw":str(supply),\n        "largest_account_count":len(rows),\n        "top1_share":float(top1/supply),\n        "top5_share":float(top5/supply),\n        "top20_share":float(top20/supply),\n        "largest_accounts":tuple(\n            {\n                "address":x.get("address"),\n                "amount":x.get("amount"),\n                "decimals":x.get("decimals"),\n                "ui_amount_string":x.get("uiAmountString"),\n            }\n            for x in rows[:20]\n        ),\n        "rpc_url":_rpc_url(),\n        "commitment":"finalized",\n    }\n\n    observation=build_independent_crypto_observation(\n        source_id="source.onchain.solana.holder_concentration."+token_address,\n        provider="solana_mainnet_rpc",\n        source_class="holder_concentration",\n        subject=token_address,\n        observation_type="solana_token_holder_concentration",\n        payload=payload,\n    )\n    if not verify_independent_crypto_observation(observation):\n        raise RuntimeError("OAD-252 provenance verification failed")\n    return observation\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_265_solana_token_holder_concentration_intelligence import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        o=acquire_solana_holder_concentration()\n        p=o.payload\n        print("[PHYSICAL] token=",p["token_address"])\n        print("[PHYSICAL] largest_accounts=",p["largest_account_count"])\n        print("[PHYSICAL] top1_share=",p["top1_share"])\n        print("[PHYSICAL] top5_share=",p["top5_share"])\n        print("[PHYSICAL] top20_share=",p["top20_share"])\n        print("[PHYSICAL] commitment=",p["commitment"])\n        self.assertGreater(p["largest_account_count"],0)\n        self.assertGreaterEqual(p["top5_share"],p["top1_share"])\n        self.assertGreaterEqual(p["top20_share"],p["top5_share"])\n        self.assertTrue(verify_independent_crypto_observation(o))\n        self.assertFalse(EXECUTION_AUTHORITY)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-265 rate-limit-resilient live Solana holder concentration certified")\n    print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")\n'
DEPENDENCIES=[
    "qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py",
    "qseries_v2/oracle_adapters/independent/oad_264_solana_token_mint_authority_supply_intelligence.py",
]

def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-265 SOLANA TOKEN HOLDER CONCENTRATION RATE-LIMIT RESILIENT REBUILD INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel in DEPENDENCIES:
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        print("[PASS] dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+module.stem+" import *"
        if export not in lines:
            lines.append(export)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] failed OAD-265 implementation replaced in-place")
        print("[PASS] HTTP 429 Retry-After handling installed")
        print("[PASS] bounded exponential retry installed")
        print("[PASS] inter-request pacing installed")
        print("[PASS] SOLANA_RPC_URL override supported")
        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
        print("[DONE] OAD-265 REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
