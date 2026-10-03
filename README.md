# FastSH

A small shell tool for running common inspection commands with a fast command check.

FastSH checks commands such as `ls`, `cat`, and `git status` before running them.
Commands it refuses can be handed back to your coding agent's usual shell tool.
Use it directly from a terminal or connect it to an agent through MCP.

**Status:** experimental beta. The checks are intended for read-only work, but
FastSH is not a security sandbox. See [limitations](#limitations).

## Quick start

Requires Python 3 and Bash. The basic gate has no Python package dependencies.
From this repository, run:

```sh
python3 q "ls -la"
python3 q "git status --short && git log --oneline -5"
```

For an interactive prompt:

```sh
python3 q
```

Enter a command to see its output. Enter `exit` to quit.
If FastSH prints `ESCALATE`, use your normal agent or shell workflow to review
and run the command.

## Connect to OpenCode

Add a `fastsh` entry to the `mcp` section of your OpenCode configuration.
Replace the example path with the absolute path to this repository:

```json
{
  "mcp": {
    "fastsh": {
      "type": "local",
      "command": ["python3", "/absolute/path/to/fastsh/mcp_fastsh.py"],
      "enabled": true
    }
  }
}
```

Restart OpenCode, then use the `fastsh` tool for inspection commands.
`FASTSH REFUSED` means the command needs your usual shell workflow.
Other MCP clients can launch the same Python script as a stdio server.

### Existing installer

`./setup.sh` registers the MCP server, installs an OpenCode permission plugin,
and starts the Laya daemon through a systemd user service.

The installer currently assumes a local Laya installation and model, an
OpenCode plugin package, and a `codegraph` entry in your OpenCode config.
Its default paths match the development machine, so review it before use.
`LAYA_VENV` points to the Python `site-packages` directory containing `laya`;
`LAYA_MODEL` points to the model directory. Even `--no-daemon` currently requires
those paths to exist.

## How it works

1. **Command gate:** rules reject known risky patterns and check supported commands.
2. **Optional classifier:** if the gate cannot accept a command and has not explicitly
   denied it, FastSH asks the resident Laya model for a verdict.
3. **Run or escalate:** accepted commands run in Bash; other commands are refused.

Without a running Laya daemon, only the command gate is available.
Check a gate decision without executing the command:

```sh
python3 fastgate.py "git status --short"
```

With the systemd service installed, control the classifier using:

```sh
./ldaemon on
./ldaemon off
./ldaemon status
```

## Performance and findings

These measurements were recorded on the development machine, an RTX 3050 Ti
laptop. They describe different parts of the workflow, not overall agent speedups.

| Measurement | Recorded result |
| --- | --- |
| Deterministic command gate | About 0.03 ms per check |
| Resident Laya classifier | About 37 ms per verdict |
| Standalone `q` command | About 30 ms end to end for measured examples |
| Gate coverage on a 200-command replay | About 16% |
| Gate plus classifier coverage on that replay | About 36% |
| OpenCode A/B experiment | No net improvement in overall task time |

Coverage is the fraction of replay commands accepted by the fast path. It is
not a measure of safety or classification accuracy.

### Why a faster tool did not make the agent faster

In the recorded baseline, trivial agent tasks took a median of about 6.2 seconds,
while the underlying commands took 1–12 ms. The experiments attributed much of
the delay to model deliberation before the tool call.

Replacing the shell tool with FastSH left that deliberation step in place, so
the A/B test showed no net task-time improvement. The standalone `q` loop avoids
that step because the user supplies the command directly. It does not choose
commands or complete coding tasks autonomously.

Further agent speed gains require reducing model turns or changing who controls
the execution loop. Faster command checking alone did not resolve the measured
bottleneck.

See [the proving log](docs/PROVING.md) for the experiment history, including
negative results, and [baseline/](baseline/) for recorded results and replay data.

## Limitations

- The gate uses regular expressions and a small shell splitter. It does not
  fully parse Bash or enforce operating-system isolation.
- Some allowed commands have mutating options that the argument rules do not
  block, including `sort -o`, `git branch <name>`, and `git remote add`.
- The optional classifier can approve commands outside the deterministic
  allowlist. Confidence thresholds do not guarantee safe execution.
- File reads can include sensitive files such as `.env`. FastSH does not enforce
  a path policy or redact secrets.
- Commands have a 15-second timeout and returned output is truncated to 8,000
  characters. Long-running or interactive commands may fail.
- The installer and systemd service need portability work for other machines.

Use FastSH in a trusted development environment with appropriate external
permissions or sandboxing. Stronger argument validation is needed before
relying on it as a read-only enforcement boundary.

## Project files

| File | Purpose |
| --- | --- |
| [fastgate.py](fastgate.py) | Deterministic command checks |
| [mcp_fastsh.py](mcp_fastsh.py) | MCP server, classifier fallback, and execution |
| [q](q) | Standalone command runner and interactive prompt |
| [laya_daemon.py](laya_daemon.py) | Resident classifier over a Unix socket |
| [ldaemon](ldaemon) | Systemd daemon controls |
| [setup.sh](setup.sh) | Installer for the development setup |
| [plugin/fastallow.ts](plugin/fastallow.ts) | OpenCode permission plugin template |
| [skill/SKILL.md](skill/SKILL.md) | Agent guidance for fewer tool turns |
| [docs/PROVING.md](docs/PROVING.md) | Detailed experiment log |

## License

[MIT](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for release notes.
