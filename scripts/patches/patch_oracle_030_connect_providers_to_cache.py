from pathlib import Path

root = Path.cwd()

engine_file = root / "oracle_research_engine.py"

if not engine_file.exists():
    print("[ERROR] oracle_research_engine.py not found")
    raise SystemExit

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle030_backup"
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

if "from oracle_provider_registry import oracle_provider_registry" not in text:
    text = "from oracle_provider_registry import oracle_provider_registry\n" + text
    print("[OK] Added provider registry import")

if "from oracle_market_cache import oracle_market_cache" not in text:
    text = "from oracle_market_cache import oracle_market_cache\n" + text
    print("[OK] Added market cache import")

old = '''    def refresh(self):
        """
        Safe first version:
        - Does not call APIs yet.
        - Prepares the shared cache structure.
        - Later builds will plug live market reads into this method.
        """
        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = self.snapshot.get("markets_checked", 0)
            self.snapshot["opportunities"] = self.snapshot.get("opportunities", [])
            self.snapshot["errors"] = self.snapshot.get("errors", [])[-10:]
'''

new = '''    def refresh(self):
        """
        ORACLE-030:
        Pull data from registered providers and store returned markets
        in the shared Oracle market cache.
        """
        provider_results = oracle_provider_registry.fetch_all()
        markets_checked = 0
        provider_errors = []

        for result in provider_results:
            provider_name = result.get("provider", "unknown")
            markets = result.get("markets", []) or []
            errors = result.get("errors", []) or []

            for error in errors:
                provider_errors.append({
                    "provider": provider_name,
                    "error": str(error),
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                })

            for market in markets:
                ticker = market.get("ticker") or market.get("market_ticker")
                if not ticker:
                    continue

                market["provider"] = provider_name
                market["cached_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                oracle_market_cache.update_market(ticker, market)
                markets_checked += 1

        cache_count = oracle_market_cache.market_count()

        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = cache_count
            self.snapshot["provider_results"] = provider_results
            self.snapshot["errors"] = (self.snapshot.get("errors", []) + provider_errors)[-10:]
            self.snapshot["opportunities"] = self.snapshot.get("opportunities", [])
'''

if old not in text:
    print("[ERROR] Could not find original refresh() block.")
    print("No changes made.")
    raise SystemExit

text = text.replace(old, new, 1)

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-030 connected providers to market cache")