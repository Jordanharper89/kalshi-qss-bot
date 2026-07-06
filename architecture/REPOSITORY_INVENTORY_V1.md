\# Repository Inventory V1



\## Purpose



Classify every top-level file and folder before any further repository migration.



\## Status Types



\- ACTIVE

\- LEGACY

\- ARCHIVE

\- BUILD

\- TEST

\- SCRIPT

\- DOCUMENTATION

\- RUNTIME

\- UNKNOWN



\## Current Known Folders



| Path | Status | Notes |

|---|---|---|

| qseries\_v2/ | ACTIVE | Main Q Series V2 platform source tree |

| qseries\_v2/oracle\_intelligence/ | ACTIVE | Oracle Intelligence active module tree |

| oracle/ | UNKNOWN | Needs review before migration |

| oracle\_data\_providers/ | ACTIVE | Oracle data provider support |

| services/ | ACTIVE | Service layer |

| plugins/ | ACTIVE | Plugin layer |

| sports/ | ACTIVE | Sports engine support |

| builds/ | BUILD | Build installers |

| tests/ | TEST | Test files |

| scripts/ | SCRIPT | Patch, runner, maintenance, and inspection utilities |

| architecture/ | DOCUMENTATION | Repository and system architecture docs |

| archive/ | ARCHIVE | Historical material |

| runtime/ | RUNTIME | Runtime/generated data; should generally stay ignored |



\## Current Root-Level Categories



\### Active / likely active source



\- ai\_answer.py

\- ai\_search.py

\- alert\_engine.py

\- categories.py

\- category\_engine.py

\- category\_validator.py

\- config.py

\- crypto\_sources.py

\- edge\_engine.py

\- edge\_strategy.py

\- external\_research.py

\- final\_trade\_decision.py

\- find\_fast\_events.py

\- get\_chat\_id.py

\- grading.py

\- journal\_ui.py

\- kalshi\_api.py

\- kalshi\_auth.py

\- kalshi\_orders.py

\- kalsi\_orders.py

\- kq\_scan\_rescue.py

\- limit\_order\_ui.py

\- live\_watch.py

\- logger.py

\- market\_memory.py

\- mlb\_engine.py

\- navigation.py

\- near\_miss.py

\- notification\_ui.py

\- open\_orders\_panel.py

\- order\_preview.py

\- orderbook.py

\- position\_cards.py

\- position\_manager.py

\- position\_monitor.py

\- position\_ui.py

\- probability\_engine.py

\- scalp\_dashboard.py

\- scanner.py

\- set\_telegram\_commands.py

\- source\_config.py

\- sport\_router.py

\- sports\_engine.py

\- strategy\_manager.py

\- strategy\_ui.py

\- system2\_overreaction.py

\- system3\_convergence.py

\- telegram\_bot.py

\- telegram\_oracle\_feed\_command.py

\- telegram\_oracle\_feed\_formatter.py

\- telegram\_queue.py

\- telegram\_text\_guard.py

\- test\_kalshi\_events\_endpoint.py

\- trade\_settings.py

\- weather\_engine.py

\- weather\_forecast\_engine.py

\- weather\_market\_parser.py



\### Legacy / needs review



\- oracle\_\*.py root-level files

\- oracle/ folder

\- archive/ folder

\- bootstrap\_qseries\_v2.py



\### Already classified



\- builds/ = BUILD

\- tests/ = TEST

\- scripts/ = SCRIPT

\- architecture/ = DOCUMENTATION



\## RAP-001 Rule



No additional file moves until this inventory is reviewed.

