"""MTR-161: offline native two-leg unsigned artifact assembly."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from .mtr_160_native_unsigned_compiler import compile_unsigned, CANONICAL, UnsignedCompileHold
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

class AssemblyHold(ValueError):
    pass

def assemble(package):
    if not isinstance(package, dict):
        raise AssemblyHold("PACKAGE_REQUIRED")
    if package.get("direction") not in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        raise AssemblyHold("DIRECTION_INVALID")
    if type(package.get("size_lamports")) is not int or package["size_lamports"] not in (
        10000000, 15000000, 20000000, 25000000, 30000000
    ):
        raise AssemblyHold("SIZE_POLICY_VIOLATION")
    ixs = package.get("instructions")
    if not isinstance(ixs, list) or len(ixs) < 2:
        raise AssemblyHold("TWO_NATIVE_INSTRUCTIONS_REQUIRED")
    pump = getattr(core, "PUMP", None)
    dlmm = getattr(core, "DLMM", None)
    if not pump or not dlmm or pump == dlmm:
        raise AssemblyHold("CANONICAL_PROGRAM_IDS_UNAVAILABLE")
    programs = [x.get("programId") if isinstance(x, dict) else None for x in ixs]
    if programs.count(pump) != 1 or programs.count(dlmm) != 1:
        raise AssemblyHold("EXACTLY_ONE_OF_EACH_SWAP_PROGRAM_REQUIRED")
    first, second = programs.index(pump), programs.index(dlmm)
    if package["direction"] == "PUMP_TO_METEORA" and not first < second:
        raise AssemblyHold("SWAP_ORDER_MISMATCH")
    if package["direction"] == "METEORA_TO_PUMP" and not second < first:
        raise AssemblyHold("SWAP_ORDER_MISMATCH")
    for ix in ixs:
        if not isinstance(ix, dict) or not isinstance(ix.get("accounts"), list):
            raise AssemblyHold("NATIVE_INSTRUCTION_INVALID")
        try:
            if not base64.b64decode(ix["data"], validate=True):
                raise AssemblyHold("EMPTY_INSTRUCTION_DATA")
        except (KeyError, ValueError) as exc:
            raise AssemblyHold("INSTRUCTION_DATA_INVALID") from exc
    alt = package.get("alt_snapshot")
    if not isinstance(alt, dict) or CANONICAL not in alt:
        raise AssemblyHold("CANONICAL_ALT_DATA_REQUIRED")
    try:
        compiled = compile_unsigned(package["payer"], ixs, package["blockhash"], alt)
    except (KeyError, UnsignedCompileHold, ValueError, TypeError) as exc:
        raise AssemblyHold("NATIVE_COMPILATION_HOLD") from exc
    return compiled

def stage(package, output):
    compiled = assemble(package)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    raw = compiled["raw"]
    txpath = output / "mtr_161_unsigned_atomic_v0.b64"
    reportpath = output / "mtr_161_unsigned_atomic_v0.json"
    report = {
        "direction": package["direction"],
        "size_lamports": package["size_lamports"],
        "transaction_sha256": hashlib.sha256(raw).hexdigest(),
        "instruction_count": compiled["details"]["instruction_count"],
        "referenced_tables": compiled["details"]["table_ids"],
        "unsigned": True,
        "native_instruction_layout_only": True,
        "official_protections_verified": False,
        "trusted_alt_evidence_linked": False,
        "simulation_passed": False,
        "profit_certified": False,
        "broadcast_authorized": False,
    }
    txpath.write_text(base64.b64encode(raw).decode("ascii") + "\n", encoding="ascii")
    reportpath.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report, txpath, reportpath

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--package", type=Path)
    p.add_argument("--output", type=Path,
                   default=Path.cwd()/"runtime_state/oracle/oracle_live_execution")
    args=p.parse_args(argv)
    if args.package is None:
        print("[MTR161] OFFLINE_TWO_LEG_UNSIGNED_ASSEMBLER_READY")
        print("[MTR161_ARTIFACT] HOLD_REAL_INSTRUCTION_PACKAGE_REQUIRED")
    else:
        try:
            if args.package.stat().st_size > 100000:
                raise AssemblyHold("INPUT_TOO_LARGE")
            package=json.loads(args.package.read_text(encoding="utf-8"))
            result, tx, report=stage(package,args.output)
        except (AssemblyHold, OSError, ValueError, KeyError) as exc:
            raise SystemExit("[HOLD] MTR161_UNSIGNED_ASSEMBLY_REFUSED: " + type(exc).__name__) from exc
        print("[MTR161_TRANSACTION_SHA256]",result["transaction_sha256"])
        print("[MTR161_ARTIFACT]",tx)
        print("[MTR161_EVIDENCE]",report)
    print("[ATOMIC_TWO_LEG_PROOF] FALSE")
    print("[PROTECTED_PROFIT] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__=="__main__":
    main()
