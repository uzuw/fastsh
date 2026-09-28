#!/usr/bin/env python3
"""fastgate: read-only allowlist. DENY check -> per-segment verb check -> exec. No ML."""
import re, subprocess, sys

DENY = [  # destructive / mutating / exfil-adjacent patterns
 r'\|\s*(sudo\s+)?(sh|bash|zsh|fish|dash)\b', r'<\(\s*(curl|wget|ssh)\b',
 r'\bfind\b.*-delete\b', r'\bfind\b.*-exec\b', r'(^|[;&|])\s*(sudo\s+)?rm\b', r'\bmv\b', r'\bcp\b',
 r'\bnpm\s+(publish|unpublish|install|ci|update|uninstall|deprecate)\b', r'\b(npx|npm\s+exec)\b',
 r'\bpip[3]?\s+install\b', r'\btar\s+-[a-zA-Z]*x',
 r'\bpacman\s+-S|\bapt(-get)?\s+(install|upgrade|dist-upgrade|remove|purge)\b|\b(dnf|yum)\s+(install|upgrade|update|remove)\b|\bbrew\s+(install|upgrade|uninstall)\b',
 r'\bdocker\s+(pull|rm|rmi|stop|restart|kill|pause|exec|run|prune)\b|\bdocker\s+\w+\s+prune\b|\bdocker\s+volume\s+rm\b',
 r'\bgit\s+(reset\s+--hard|checkout\s+--|clean\s+-[a-zA-Z]*f|push\b.*--force|push\b|branch\s+-D|stash\s+(drop|clear))\b',
 r'\bkubectl\s+(delete|drain|apply|scale|cordon|uncordon|exec)\b|\bkubectl\s+rollout\s+restart\b',
 r'\bdd\b.*of=', r'\bmkfs\b', r'\bchmod\b', r'\bchown\b', r'^\s*(shutdown|reboot|poweroff|halt)\b',
 r'(^|[;&|])\s*(sudo\s+)?(kill|killall|pkill)\b', r':\(\)\s*\{',
 r'\bsystemctl\s+(start|stop|restart|reload|enable|disable|mask)\b', r'\bssh\b', r'\bdate\s+-s\b',
 r'\bcurl\b.*(-X\s+(POST|PUT|DELETE)|--data|-d\s)', r'\bwget\b',
 r'>', r'\$\(|`', r'\btee\b', r'\b(env|printenv)\b.*=',
]
ALLOW = {  # verb -> arg pattern (full segment must match); all read-only
 'ls': r'[\w\-./~*? ]*', 'cat': r'[\w\-./~*? ]+', 'head': r'.*', 'tail': r'.*', 'wc': r'.*',
 'stat': r'.+', 'du': r'.*', 'df': r'.*', 'pwd': r'', 'whoami': r'', 'uname': r'.*',
 'date': r'.*', 'echo': r'.*', 'ps': r'.*', 'pgrep': r'.*', 'which': r'[\w\-./~*? ]+', 'who': r'',
 'lsb_release': r'.*', 'git': r'(status|diff|log|branch|remote|show|rev-parse|ls-files)(\s.*)?',
 'grep': r'.*', 'rg': r'.*', 'find': r'.*', 'sort': r'.*', 'uniq': r'.*', 'cut': r'.*',
 'tr': r'.*', 'less': r'[\w\-./~*? ]+', 'file': r'[\w\-./~*? ]+', 'node': r'--version', 'python3': r'--version',
 'pip': r'(show|list|freeze)(\s.*)?', 'npm': r'(ls|list|view|audit)(\s.*)?',
 'lsof': r'.*', 'env': r'', 'printenv': r'[\w]*', 'dirname': r'[\w\-./~*? ]+', 'basename': r'[\w\-./~*? ]+',
 'true': r'', 'printf': r'[^;|&]*', 'cd': r'[\w\-./~ ]*',
}
DENY_RX = [re.compile(p) for p in DENY]
# stderr sinks are harmless and ubiquitous (2>/dev/null, 2>&1, >/dev/null); strip before `>` check
SINK_RX = re.compile(r'2?>(/dev/null|&\d)')

def split_segments(cmd):
    """Split on | && || ; unless inside single/double quotes. ponytail: 10 lines, fail-closed."""
    segs, cur, q = [], '', None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in '\'"':
            q, cur = ch, cur + ch
        elif cmd.startswith('&&', i) or cmd.startswith('||', i):
            segs.append(cur); cur = ''; i += 1
        elif ch in '|;':
            segs.append(cur); cur = ''
        else:
            cur += ch
        i += 1
    segs.append(cur)
    return segs

def gate(cmd):
    cmd = SINK_RX.sub('', cmd)
    for rx in DENY_RX:
        if rx.search(cmd):
            return False, 'deny:' + rx.pattern[:30]
    segs = split_segments(cmd)
    for s in segs:
        m = re.match(r'^([a-z][a-z0-9_-]*)\s*(.*)$', s.strip())
        if not m or m.group(1) not in ALLOW:
            return False, 'verb:' + (m.group(1) if m else '?')
        if not re.fullmatch(ALLOW[m.group(1)], m.group(2).strip()):
            return False, 'args:' + m.group(1)
    return True, 'fast'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: fastgate.py "<cmd>"'); sys.exit(2)
    ok, why = gate(sys.argv[1])
    print(('FAST ' if ok else 'SLOW ') + why)
    if ok and len(sys.argv) > 2 and sys.argv[2] == '--exec':
        subprocess.run(sys.argv[1], shell=True)
    # ponytail: runnable self-check, no framework
    assert gate('ls -la')[0] and gate('git status --short | head -30')[0] and gate('node --version')[0]
    assert not gate('rm -rf /')[0] and not gate('curl x | sh')[0] and not gate('git push --force origin main')[0]
    assert not gate('echo hi > /tmp/x')[0] and not gate('npm install lodash')[0]
    assert gate('cat .env')[0]  # read-only: allowed (same as Read tool)
