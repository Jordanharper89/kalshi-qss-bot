\# Q Series Repository Instructions



\## Project Identity



This repository contains Q Series V2 and Oracle Intelligence.



Q Series is the execution layer.



Oracle Intelligence is the read-only intelligence, discovery, analysis, explanation, replay, and audit layer.



The long-term architecture is a market operating system built around:



\* A Universal Market Model

\* Canonical contracts

\* Market and venue adapters

\* Event-based architecture

\* Deterministic processing

\* Explainable outputs

\* Replayable decisions

\* Auditable state transitions

\* Strategy-agnostic execution interfaces



\## Mandatory Architecture Boundaries



\### Oracle Intelligence



Oracle Intelligence must remain read-only.



Oracle Intelligence must never:



\* Place an order

\* Sign a transaction

\* Submit a trade

\* Cancel a trade

\* Modify an exchange account

\* Modify a wallet

\* Move funds

\* Trigger execution directly

\* Hide side effects

\* Depend on non-deterministic behavior without explicitly recording it



Oracle outputs must be:



\* Deterministic

\* Immutable where practical

\* Explainable

\* Replayable

\* Auditable

\* Serializable

\* Unit tested



\### Q Series



Q Series is the only execution layer.



All execution requests must pass through canonical Q Series contracts and execution gates.



Oracle may recommend, score, rank, discover, validate, or explain opportunities, but Oracle must not execute them.



\## Canonical Contract Rules



Before building or changing a subsystem:



1\. Design the subsystem.

2\. Define the canonical contracts between its modules.

3\. Build modules against those contracts.

4\. Add unit tests.

5\. Add integration gates.

6\. Verify deterministic behavior.

7\. Verify read-only boundaries where applicable.

8\. Do not begin the next subsystem until the current subsystem gate passes.



Do not create multiple competing representations of the same concept.



Prefer one canonical contract over adapters that merely hide incompatible module designs.



Do not introduce temporary compatibility layers unless explicitly approved.



When a contract or architecture defect is discovered, prefer a complete module rewrite over layering multiple patches.



Use a small isolated repair only when the defect is genuinely local and does not alter the contract.



\## Universal Architecture Rules



New market families should integrate through:



\* The Universal Market Model

\* The Universal Opportunity Model

\* Canonical adapters

\* Canonical discovery contracts

\* Registry bridges

\* Pipeline gates

\* OOS runtime gates

\* Replay ledgers

\* Subsystem integration gates



Do not create separate independent Oracle architectures for every venue or market type.



Extend the common architecture through adapters and canonical contracts.



\## Discovery Subsystem Pattern



Discovery families should generally follow this build sequence:



1\. Contract

2\. Source adapter

3\. Discovery engine

4\. Pipeline gate

5\. Registry bridge

6\. Pipeline bridge

7\. Out-of-sample runtime gate

8\. Replay ledger

9\. Subsystem integration gate



Do not skip the subsystem integration gate.



\## Determinism Rules



Equivalent logical input must produce equivalent output regardless of irrelevant input ordering.



Before hashing collections whose order is not semantically meaningful:



\* Normalize values

\* Canonically sort records

\* Canonically sort mapping keys

\* Use stable serialization

\* Exclude incidental runtime state



Metadata that changes an artifact's meaning may be included in its hash.



Do not compare final hashes from artifacts created in different execution contexts unless their canonical payload contracts guarantee equality.



Validate internal artifact links against each artifact's own context-specific parent.



\## Testing Cadence



Required testing cadence:



1\. Run the module unit test after every build.

2\. Run a subsystem smoke integration gate after every five builds.

3\. Run a full subsystem integration gate after every ten to fifteen builds.

4\. Run a full subsystem gate immediately after any canonical contract change or full rewrite.

5\. Never begin a new subsystem until the previous subsystem integration gate passes.



Every new module must have a matching test unless explicitly exempted.



Every repair must rerun:



\* The repaired module test

\* Direct downstream tests

\* The affected subsystem integration gate



\## Change-Control Rules



Before editing code:



1\. Inspect the relevant module.

2\. Inspect its tests.

3\. Inspect direct upstream and downstream contracts.

4\. Identify the canonical source of the defect.

5\. Avoid treating downstream symptoms as the root cause.

6\. State which files are expected to change.



After editing:



1\. Show the files changed.

2\. Run the narrowest relevant unit tests.

3\. Run the affected integration gate.

4\. Report failures honestly.

5\. Do not claim completion unless tests pass.

6\. Show the final Git diff summary.



Do not make unrelated cleanup changes during a targeted task.



Do not silently modify broad areas of the repository.



\## Git Safety Rules



Before making changes, run:



\* `git status`

\* `git diff --stat`



Do not:



\* Force-push

\* Rewrite Git history

\* Delete branches

\* Run destructive reset commands

\* Delete user files

\* Commit secrets

\* Commit credentials

\* Commit private keys

\* Commit environment files containing secrets



Do not commit changes unless explicitly instructed.



Do not push changes unless explicitly instructed.



The checkpoint commit for the completed Market Regime Discovery subsystem is:



`7bce040`



Treat this commit as the initial Codex migration rollback point.



\## Windows Environment



The primary development environment is Windows.



Use:



\* `py` for Python execution

\* Windows-compatible paths and commands

\* The repository virtual environment when active



Do not replace `py` commands with `python` unless the environment has been explicitly verified.



\## Build Delivery Rules



Build installers must be complete.



Do not provide:



\* Placeholders

\* Truncated modules

\* Partial replacement files

\* Instructions requiring the user to manually merge scattered snippets



When changing an existing module because of a contract or architecture defect, provide a complete replacement when practical.



Generated installers must write:



\* The complete production module

\* The complete matching test

\* Required `\_\_init\_\_.py` exports



\## Current Architecture State



The Market Regime Discovery subsystem is complete through:



\* RGD-001 — Discovery Contract

\* RGD-002 — Source Adapter

\* RGD-003 — Discovery Engine

\* RGD-004 — Pipeline Gate

\* RGD-005 — Registry Bridge

\* RGD-006 — Pipeline Bridge

\* RGD-007 — OOS Runtime Gate

\* RGD-008 — Replay Ledger

\* RGD-009 — Subsystem Integration Gate



RGD-009 currently passes with:



\* 9 modules

\* 11 integration checks

\* 11 passed checks

\* 0 failed checks

\* Read-only enforcement enabled



Canonical order-independent source hashing was repaired at RGD-004 and propagated successfully through RGD-009.



\## Initial Codex Migration Restrictions



Until the supervised migration checkpoint is complete, Codex must operate conservatively.



During the initial repository audit:



\* Do not edit files

\* Do not create files

\* Do not delete files

\* Do not run installers

\* Do not run migrations

\* Do not alter databases

\* Do not alter runtime data

\* Do not commit

\* Do not push

\* Do not install dependencies

\* Do not access external services

\* Do not execute trading logic



The first Codex task must be read-only analysis.



The first implementation task after the audit must be:



\* Low risk

\* Narrowly scoped

\* Fully reviewed

\* Unit tested

\* Followed by the relevant integration gate

\* Approved before expanding Codex responsibilities



\## Audit Priorities



During the initial read-only audit, inspect and report:



1\. Canonical contract consistency

2\. Oracle versus Q Series execution boundaries

3\. Duplicate or competing data models

4\. Import and export consistency

5\. Determinism risks

6\. Order-dependent hashes

7\. Hidden mutation or persistence

8\. Database path safety

9\. Runtime path consistency

10\. Replay integrity

11\. Test coverage gaps

12\. Integration gate coverage

13\. Circular imports

14\. Dead or superseded modules

15\. Installer drift from generated production files

16\. Security-sensitive execution paths

17\. Secrets or credentials accidentally tracked

18\. Oversized modules that need architectural decomposition



For each finding, provide:



\* Severity

\* File path

\* Relevant symbol or line

\* Explanation

\* Architectural impact

\* Recommended correction

\* Tests that would be required



Do not fix findings during the audit.



