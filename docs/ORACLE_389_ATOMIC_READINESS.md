# ORACLE-389 — Scanner/Executor Revision Contract and Live Readiness

## Authority and scope

- **Installed scanner**: ORACLE-388 scanner source, pinned by SHA-256. No scanner rewrite in ORACLE-389.
- **Purpose of ORACLE-389**: replace obsolete ORACLE-360 / ORACLE-363 source audits that incorrectly reject the certified scanner revision; preserve the same SQLite bus, independent scanner, and original Q18/Q20/Q25 files.
- **Execution**: audit/certification only. This release does not authorize private-key use, transaction signing, sending, or broadcasting. `ORACLE385` remains a read-only candidate-consumption and preflight path. Do not describe it as a live sender.

## Exact size contract

1. Scanner prices 19 sizes, 0.010, 0.015, ..., 0.100 SOL in both PUMP_TO_METEORA and METEORA_TO_PUMP directions.
2. Scanner picks the **highest quoted gross lamport opportunity** per direction, not necessarily the final fee-adjusted optimal size. The exact size is published as integer `size_lamports` to `runtime_state/oracle/final_boss_dual/candidate_bus.sqlite3`.
3. Executor reads the original scanner nomination from SQLite using scanner producer+epoch, market identity, direction, source timestamp and slot. An old 0.010 nomination or unrelated 0.010 native template is not proof that the selected size was preserved.
4. Reject out-of-range amounts, stale/replayed entries, incorrect pool or token, mismatched size, failed quotes, and incomplete Meteora bin-array fills. Keep both directions independently.
5. Reprice the **same size** against an internally consistent pool snapshot and only proceed if net profit after complete realistic fees and token residues is positive. Do not silently substitute 0.010 for 0.035 or 0.100. If size is unaffordable, HOLD.
6. First funded **live canary policy remains exactly 0.010 SOL**, subject to a separate explicit live-authorization gate. The canary policy is distinct from the scanner's 0.010–0.100 search. A non-0.010 nominated trade cannot be quietly resized to meet that gate; either find and independently certify a genuine 0.010 trade or HOLD.

## Admission and profitability gates before enabling LIVE

- All source hashes/frozen Q18/Q20/Q25 checks pass; ORACLE-385 audit and health gate pass with a live producer.
- Real source data: PumpSwap and Meteora exact pool identities, full hydrated DLMM arrays and Token-2022 transfer requirements; no constant-product approximation for PumpSwap.
- Exact selected size matches each native leg, WSOL/token input/output, transaction instructions and compiled v0+ALT accounts.
- Fee and economics: base signature fee, *requested* compute-unit priority fee, rent/ATA setup, SOL wrapping, relay/tips if any, slippage reserve, residual tokens and safe wallet reserve all deducted consistently; exclude partial fills.
- Signed simulation on a constructed atomic v0 transaction with real payer and current blockhash, appropriate compute budget, positive post-fee net, and no token residue or simulation errors. A standalone `--node-check` or unsigned syntax check is insufficient.
- Revalidate state freshness and profitability immediately before broadcast. Ensure blockhash and ALT validity, idempotent submission, bounded retries and tracking to confirmed/finalized outcome.
- Reconcile wallet balances, token balances, fees and rent after inclusion. Define emergency stop and funded-loss cap. Fees can be charged even for transactions whose instructions fail.
- Only after these gates are observed in live evidence should a separate dedicated live-authority implementation be considered. ORACLE-389 and ORACLE-385 cannot create live execution authorization.

## Proven evidence as of this release

- User's bounded ORACLE-322 run: `raw=43`, `exact_pairs=14`, rejected `NO_DLMM_PAIR=29`; `admitted=14` and 307 watched accounts. Number of eligible pairs varies with discovery, not hardcoded to 28.
- Exactly six scanner nominations in that run; selected amounts included 0.035 SOL and 0.100 SOL. SQLite confirmed the selected amounts, but **no certified atomic net-positive live trade** was reported.
- ORACLE-385 last blocked at `AUDIT_FAILED_FROZEN_SCANNER_SHA_MATCH`, a versioned source-audit dependency. The ORACLE-389 installer upgrades the audit contract, not the scanner.

## Windows CMD release procedure

Stop the executor; do not interrupt the independently running scanner solely to install this release. Run in the activated venv from repo root:

```bat
python build_oracle_389_scanner_revision_audit_migration.py --test && python build_oracle_389_scanner_revision_audit_migration.py --audit && python build_oracle_389_scanner_revision_audit_migration.py --install && python build_oracle_389_scanner_revision_audit_migration.py --verify
python build_oracle_360_integrity_bus_recovery.py --install && python build_oracle_360_integrity_bus_recovery.py --audit
python build_oracle_363_scanner_bus_binding_replacement.py --audit && python build_oracle_385_scanner_source_unification.py --audit
python build_oracle_389_scanner_revision_audit_migration.py --readiness
```

`--readiness` is read-only. It reports scanner health and current selected-size events but does not certify simulation, wallet capacity, economics or signing. Do not run old ORACLE-387/388 `--verify` after the versioned ORACLE-389 ingress audit replacement; ORACLE-389 owns the composite version manifest.

## Authoritative external references (checked October 2026)

- Solana transaction atomicity: https://solana.com/docs/core/transactions
- Solana fee accounting (including failed-transaction fees): https://solana.com/docs/core/fees/fee-structure
- Solana compute budget / priority fee accounting: https://solana.com/docs/core/fees/compute-budget
- Solana production readiness: https://solana.com/docs/tools/production-readiness
- Meteora official DLMM SDK quote/full-consumption and bin-array API: https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/reference.mdx
- Meteora DLMM SDK usage examples: https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/examples.mdx
