---
name: few-turns
description: Minimize turns per task — batch reads into compound fastsh commands, never re-read shown output, stop at first sufficient evidence.
---

# Few-turns: minimize turns, not seconds

Latency data: trivial shell tasks cost ~6s LLM deliberation vs 1ms exec. Turns are the cost. One compound read beats five single reads.

## Rules

1. **One inspection turn, not five.** Batch with `&&`, `||`, `;`, `|` into a single `fastsh` call. Prefer one call with 4 probes over 4 calls.
2. **fastsh-first for reads.** Any read-only check goes to `fastsh`, never a heavyweight tool or a separate turn per file.
3. **Never re-read shown output.** If a prior result contains it, quote it. No second call to "confirm".
4. **Stop at first sufficient evidence.** Sufficiency beats completeness. Don't enumerate the repo when one file answers.

## Compound patterns (all fastgate-FAST)

```sh
git status --short && git log --oneline -5 && git diff --stat
ls && cat package.json | head -50
ps aux | grep -i node | head -20
ls src && wc -l src/*.ts 2>/dev/null | sort -n | tail -5
cat FILE 2>/dev/null || find . -maxdepth 2 -name "FILE*" | head
du -sh * 2>/dev/null | sort -h | tail -10 && df -h .
git ls-files | head -30 && git remote -v
```

## Anti-patterns (each wastes a turn)

- `ls` alone, then `cat` alone, then `git status` alone — combine them.
- Re-`cat`ing a file already printed. Scroll up instead.
- `find / -name ...` full-tree scans when `ls` + `git ls-files` answers.
- Reaching for `npm ls` / `pip show` before `cat package.json` / `pip freeze`.

## When to spend a second turn

Only when the first output names the exact next file/command AND the task is still unanswered. Otherwise answer from what you have.
