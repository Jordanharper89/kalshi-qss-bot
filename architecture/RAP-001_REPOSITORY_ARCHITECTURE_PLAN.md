\# RAP-001 — Repository Architecture Pass



\## Goal



Organize Q Series into a professional, scalable repository without changing production code behavior.



\## Current Rule



No more Oracle builds until RAP-001 is complete.



\## Repository Principles



\- Source code must be separated from installers.

\- Tests must be separated from source.

\- Runtime/generated files must not be committed.

\- Secrets must never be committed.

\- Backups must not live in the active source tree.

\- Q Series execution code and Oracle read-only intelligence code must remain architecturally distinct.

\- Migration must happen in controlled stages.

\- No large blind `git add .` until repository structure is approved.



\## Target Layout Draft



```text

kalshi-qss-bot/

├── qseries\_v2/

├── oracle/

├── services/

├── plugins/

├── sports/

├── builds/

│   ├── oi/

│   ├── adp/

│   ├── core/

│   ├── ops/

│   └── replay/

├── tests/

│   ├── oi/

│   ├── adp/

│   ├── core/

│   └── ops/

├── scripts/

│   ├── patches/

│   ├── inspectors/

│   ├── runners/

│   └── maintenance/

├── docs/

├── architecture/

├── runtime/

└── archive/

