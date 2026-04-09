---
name: content-hash-cache-pattern
description: Cache expensive file processing results using SHA-256 content hashes — path-independent, auto-invalidating, with service layer separation.
---

# Content-Hash File Cache Pattern

> Cache expensive file processing results using SHA-256 content hashes — path-independent, auto-invalidating, with service layer separation.

## 언제 사용

- Building file processing pipelines (PDF, images, text extraction)
- Processing cost is high and same files are processed repeatedly
- Need a `--cache/--no-cache` CLI option
- Want to add caching to existing pure functions without modifying them

## 챕터 목록

| # | 챕터 | 핵심 키워드 | 파일 |
|---|------|------------|------|
| 1 | Core Pattern | Core, Pattern, {hash}.json | [chapters/01-core-pattern.md](chapters/01-core-pattern.md) |
| 2 | Key Design Decisions | Key, Design, Decisions, {hash}.json, None | [chapters/02-key-design-decisions.md](chapters/02-key-design-decisions.md) |
| 3 | Best Practices | Best, Practices | [chapters/03-best-practices.md](chapters/03-best-practices.md) |
| 4 | Anti-Patterns to Avoid | Anti-Patterns, Avoid | [chapters/04-anti-patterns-to-avoid.md](chapters/04-anti-patterns-to-avoid.md) |
| 5 | When NOT to Use | When, Use | [chapters/05-when-not-to-use.md](chapters/05-when-not-to-use.md) |

> **사용법**: 이 목차에서 필요한 챕터를 찾은 후, 해당 챕터 파일만 열어서 확인하세요.
