# Key Design Decisions

> 상위 스킬: [content-hash-cache-pattern](../SKILL.md)

| Decision | Rationale |
|----------|-----------|
| SHA-256 content hash | Path-independent, auto-invalidates on content change |
| `{hash}.json` file naming | O(1) lookup, no index file needed |
| Service layer wrapper | SRP: extraction stays pure, cache is a separate concern |
| Manual JSON serialization | Full control over frozen dataclass serialization |
| Corruption returns `None` | Graceful degradation, re-processes on next run |
| `cache_dir.mkdir(parents=True)` | Lazy directory creation on first write |
