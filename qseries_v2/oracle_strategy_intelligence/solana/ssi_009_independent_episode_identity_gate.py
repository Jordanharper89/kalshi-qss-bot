def independence(rows):
 tokens=tuple(r["token"] for r in rows if r.get("token")); unique=tuple(dict.fromkeys(tokens))
 return {"episodes":len(rows),"identified_tokens":len(tokens),"unique_tokens":unique,"independent_tokens":len(unique),"duplicates":len(tokens)-len(unique)}
