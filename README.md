# FastSH — millisecond read-only shell for coding harnesses

Coding agents spend ~6s of LLM deliberation on every trivial shell read (`ls`,
`git status`, `ps`) that executes in 1ms. FastSH is the deterministic shortcut:
a read-only gate, a resident classifier fallback, and a narrow REPL — with
fail-closed escalation to your harness on anything unsure.

| Path | Latency | Coverage |
|---|---|---|
| Regex gate (common reads) | ~0.03ms | ~16% of real traffic |
| Laya daemon (gray zone) | ~37ms | lifts to ~36% |
| `q` narrow loop (no LLM at all) | ~30ms end-to-end | same 36% |
| Escalate → OpenCode/Claude/Codex | as today | everything else |

## Install

```sh
./setup.sh
```

Backs up `~/.config/opencode/opencode.jsonc`, registers the `fastsh` MCP
server, installs the permission plugin, enables the daemon switch. Requires
python3; Laya model optional (override via `LAYA_VENV` / `LAYA_MODEL` env).
Then restart your OpenCode session.

## Use

- **In OpenCode:** call the `fastsh` tool for any read-only command. Refusals
  (`FASTSH REFUSED…`) mean: use `bash` — the command writes or is risky.
- **Standalone:** `python3 q "<command>"` for ms answers, or bare `q` for the REPL.
- **Daemon switch:** `./ldaemon on|off|status`. Off = regex only, gray zone escalates.
- **Gate check:** `python3 fastgate.py "<cmd>"` → `FAST …` / `SLOW …`.

Rules of thumb: no `>` redirects, no `$()`/backticks, no `rm|mv|cp|kill|ssh|npm install`
— those always escalate. `2>/dev/null`, globs, and quoted pipes are fine.

## Layout

- `fastgate.py` — deterministic gate (DENY + verb allowlist, fail-closed, self-checks)
- `mcp_fastsh.py` — MCP server: gate → Laya daemon fallback → exec/refuse
- `laya_daemon.py` — resident Laya classifier over unix socket (kills 17s cold load)
- `q` — narrow REPL: ms answers, `ESCALATE` on uncertainty
- `ldaemon` — daemon on/off switch (systemd user service underneath)
- `setup.sh` — idempotent plug-and-play installer
- `plugin/fastallow.ts` — OpenCode permission hook: auto-allow gate-FAST bash
- `skill/SKILL.md` — `few-turns`: compound-first agent guidance
- `docs/PROVING.md` — full measurement log, including the failed experiments
- `baseline/` — benchmark scripts, results, 200-command replay set

## Status: beta, honest numbers in `docs/PROVING.md`

Works today for read-only traffic. Known limits: `kill` always escalates;
compound-command coverage needs a fine-tune on real traffic (dataset in
`baseline/replay_clean.txt`); tools can't skip LLM deliberation — `q` exists
for that. See [CHANGELOG](CHANGELOG.md). License: MIT — see [LICENSE](LICENSE).
