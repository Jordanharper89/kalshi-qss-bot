ORACLE V1 - 2 INDEPENDENT RUNTIMES
===================================
Build 1: scanner.py - event-driven Q25/Q20/Q18 exact local pricing capture
Build 2: executor.py - existing checkpoint26 native signed-simulation wrapper

CERTIFICATION: Local compilation and deterministic fixture tests passed.
This package has NOT been validated against the user's Windows working tree,
Helius mainnet WebSocket transport, funded signed simulations, or production
transaction broadcasting. --live is deliberately denied. No guaranteed profit.

ORACLE-524 historical evidence: 8 quoted tokens matched to 8 exact pools.
ORACLE-525 physical blocker: all 8 Checkpoint-12 hydrations lacked decimals_x.
V1 includes strict on-chain decimals and pool metadata verification; this
replaces a direct dependency on uninstalled ORACLE-526. Physical mainnet
verification of those checks remains pending.

Contract & safety:
- Scanner does not accept a signer, never places orders, creates read-only
  nominations with 1500ms default expiry and SQLite WAL deduplication.
- Executor requires an existing signer ONLY to sign simulateTransaction, never
  broadcasts, never edits native production registry, and reports simulation
  count separately from verified net profitability.
- Both stop if canonical live source is missing or incompatible.
- Frozen scanner boss_scanner_live.py is never edited or relaunched by V1.
- V1 initially uses the 8 historically verified pools, NOT all 62 stage rows;
  ongoing inventory expansion is NOT yet certified.
- Candidate handoff is advisory, not proof a current atomic trade is executable.

INSTALL (Windows CMD, from repository root):
  mkdir qseries_v2\oracle_execution\solana_atomic_executor\V1
  tar -xf "%USERPROFILE%\Downloads\oracle_v1_bundle.zip" -C qseries_v2\oracle_execution\solana_atomic_executor

TEST (Windows CMD):
  python -m qseries_v2.oracle_execution.solana_atomic_executor.V1.scanner --test
  python -m qseries_v2.oracle_execution.solana_atomic_executor.V1.executor --test
  python -m qseries_v2.oracle_execution.solana_atomic_executor.V1.scanner --audit-repo

RUN: See ChatGPT response for protected hidden-key launch commands.
Open two independent CMD windows for parallel 180-second scanner and
90-second executor trial after configuring Helius RPC/WS.

Sources reviewed: public GitHub main branch tree, previous Oracle logs, attached
builds 514-524, selected prior conversations, Solana docs, Meteora DLMM docs,
and Pump official docs. This is NOT a claim that every local Oracle 001-525
source or every ChatGPT Plus message was available to inspect.

Money path requires further physical evidence: correct direct WebSocket state,
exact quote, legal native atomic v0 + ALT, sigVerify simulation, fees/slippage,
canary size exactly 0.010 SOL, recent blockhash, revalidation, actual broadcast
and finalized wallet/WSOL/token reconciliation. No broadcast until all gates.
