# Proving log — how we know what we claim

Thesis: harness slowness is decisions-per-task, not tokens-per-second. Shell is
a ~50-verb fixed grammar; classify, don't generate. Everything below was measured
on this machine (RTX 3050 Ti laptop, CPU+CUDA); failures kept, not hidden.

## P0 — Classifier steady-state: 29ms
Same-process repeat `predict`: 25.9s (load) → **29ms**. Resident-or-nothing.

## P1 — Zero-shot action: kill_proc @0.99
No examples. Classification fits the problem.

## P2 — Safety head alone: 10/15, not a gate
`curl | sh → safe @0.97`. Recovered `gate.pyc` showed the original design:
model + regex DENY + threshold. Head = ranker, regex = gate.

## P4 — Harness baseline: p50 6.2s vs 1–12ms direct (~1000× gap)
20 trivial tasks, `baseline.sh`; slowest (16.6s) was killing a process.

## P6 — laya-cli-best repaired + evaled: routing 14/15 @33ms
Bare `model.safetensors` + grafted base sidecars. Miss (`cat→git @0.77`) sits
below threshold → would escalate. Correct behavior.

## P7 — Replay kill-criterion: FAILED (24% fast, need >70%)
200 real harness commands: fine-tune is conservative on compounds, rates
code-junk as safe. First attempt void (batch API returns one answer) — redone.

## P8 — Read-only gate ships: 19/20 baseline tasks FAST, 20/20 adversarial blocked
`fastgate.py`, stdlib only. Two bugs found by measuring (bare `>` vs `2>/dev/null`;
naive `|` split vs quoted alternations). Later: glob support (`*`).

## P9 — A/B wire-up: NEGATIVE (tool effect ≈ 0)
Model used fastsh 18/19 tasks; task time unchanged net of standalone boot tax.
6s is pre-call deliberation — no tool skips it. Plugins can't add tools in
OpenCode v2 (MCP is the path); MCP lazy-loads out of base context.

## P10 — Attribution: 6s = first call on 14k context
12–13k input tokens, 3.6s to tool exec, 2 steps/task, ~100 output tokens.
fastsh arm worse (+1 discovery roundtrip, +4k tokens). Rank: skip-LLM >>
fewer-turns >> shorter-context >> gate speed. Gate inlined 27ms → 0.03ms.
`skill/SKILL.md` written for fewer-turns.

## P11 — MCP prune: 0 tokens
14,316 → 14,347. Lazy loading already excludes it.

## P13 — Tool strip -25% tokens: 0 wall time
62 → 3 tools, 14.3k → 10.8k tokens, 6.2s → 6.2s. Not token-volume-bound.

## P12/P14 — Resident Laya + narrow loop: SHIPPED
Daemon ~37ms; MCP fallback lifts replay coverage 16% → 36%, DENY-first;
permission auto-allow hook; `q` REPL: compound query 33ms, refuse 23ms.

## Scoreboard
| Lever | Result |
|---|---|
| Faster tool exec | 0 |
| MCP prune / tool strip | 0 |
| ML gate (general) | killed at 24% |
| Read-only gate + daemon + `q` | works, 36%, ms |
| Remaining +sign | smaller/faster model per turn; fine-tune on traffic; loop ownership |
