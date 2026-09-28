#!/usr/bin/env python3
"""q: the narrow loop. read-only questions answered in ms, no LLM.
Usage: q "git status --short && git log --oneline -5" | q (repl)
ESCALATE means: hand it to OpenCode. ponytail: thin over mcp_fastsh."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_fastsh import verdict

def ask(cmd):
    v = verdict(cmd)
    if v.startswith('FAST'):
        p = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, timeout=15)
        return (p.stdout + p.stderr)[:8000] or '(empty)'
    return f'ESCALATE [{v}]: hand to OpenCode'

def main():
    if len(sys.argv) > 1:
        print(ask(' '.join(sys.argv[1:])))
        return
    try:
        while True:
            cmd = input('q> ').strip()
            if cmd in ('quit', 'exit', ''):
                break
            print(ask(cmd))
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == '__main__':
    if '--selfcheck' in sys.argv:
        assert 'ESCALATE' not in ask('ls -la')
        assert ask('rm -rf /').startswith('ESCALATE')
        assert ask('cat README.md') != ''
        print('selfcheck ok')
    else:
        main()
