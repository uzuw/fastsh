# Changelog

## [0.1.0] - 2026-09-28
### Added
- `fastgate.py`: deterministic read-only gate (DENY + allowlist, fail-closed)
- `mcp_fastsh.py`: MCP server with Laya-daemon gray-zone fallback
- `laya_daemon.py` + `ldaemon` switch: resident classifier (~37ms verdicts)
- `q`: narrow REPL (compound query ~33ms, refuse ~23ms)
- `setup.sh`: idempotent installer; `plugin/fastallow.ts`: permission auto-allow
- `skill/SKILL.md`: few-turns agent guidance
- `docs/PROVING.md`: full measurement log; `baseline/`: benchmarks + replay set
### Measured
- Baseline p50 6.2s/task vs 1–12ms direct; gate 0.03ms; replay coverage 36%
- Negative results kept: ML gate 24% (killed), A/B net ≈ 0, MCP prune 0 tokens
