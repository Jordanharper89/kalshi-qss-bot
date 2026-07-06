\# Repository Folder Contracts



\## qseries\_v2/



Status: ACTIVE



Purpose:

Primary Q Series V2 platform source tree.



Allowed:

\- Active Q Series platform modules

\- Active Oracle Intelligence package

\- Active adapters

\- Active core services

\- Active ops modules



Not Allowed:

\- Build installers

\- One-off patch scripts

\- Runtime JSON state

\- Local secrets

\- Old backup files



\## qseries\_v2/oracle\_intelligence/



Status: ACTIVE



Purpose:

Canonical Oracle Intelligence source package.



Allowed:

\- OI modules

\- OI canonical contracts

\- OI integration gates

\- OI package exports



Not Allowed:

\- Root-level legacy Oracle files

\- Execution logic

\- Trading order submission

\- Runtime secrets



\## oracle/



Status: REVIEW



Purpose:

Legacy/current Oracle support folder.



Allowed:

\- Oracle support code pending classification



Not Allowed:

\- New Oracle Intelligence modules unless explicitly migrated



\## builds/



Status: BUILD



Purpose:

Historical build installers and installer generators.



Allowed:

\- build\_oi\_\*.py

\- build\_adp\_\*.py

\- build\_core\_\*.py

\- build\_ops\_\*.py

\- build\_replay\_contract\_\*.py



Not Allowed:

\- Production runtime modules

\- Secrets

\- Runtime state



\## tests/



Status: TEST



Purpose:

All standalone test files.



Allowed:

\- test\_oi\_\*.py

\- test\_adp\_\*.py

\- test\_core\_\*.py

\- test\_ops\_\*.py

\- integration gate tests



Not Allowed:

\- Production modules

\- Build installers



\## scripts/



Status: SCRIPT



Purpose:

One-off or reusable utility scripts.



Allowed:

\- patches/

\- inspectors/

\- runners/

\- maintenance/



Not Allowed:

\- Active production modules

\- Secrets

\- Runtime state



\## architecture/



Status: DOCUMENTATION



Purpose:

Architecture plans, constitutions, registries, migration plans, manuals.



Allowed:

\- Repository docs

\- Oracle docs

\- System architecture docs

\- Registry docs



Not Allowed:

\- Runtime state

\- Secrets



\## runtime/



Status: RUNTIME



Purpose:

Ignored runtime/generated outputs.



Allowed:

\- generated JSON

\- local state

\- temporary output

\- logs



Not Allowed:

\- Source code that must be versioned

\- Secrets committed to Git



\## archive/



Status: ARCHIVE



Purpose:

Historical files no longer used in active development.



Allowed:

\- old backups

\- deprecated modules

\- historical experiments



Not Allowed:

\- active source

\- current tests

\- current installers

