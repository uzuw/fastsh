#!/usr/bin/env python3
"""fastsh MCP server (stdio, stdlib only). One tool: fastsh. ponytail: minimal MCP."""
import json, os, re, socket, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOCK = os.environ.get('LAYA_SOCK', '/tmp/laya-gate.sock')
TAU = 0.9

DENY = [  # destructive / mutating / exfil-adjacent patterns (inlined from fastgate.py)
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

def verdict(cmd):
    ok, why = gate(cmd)
    if ok:
        return 'FAST regex'
    if why.startswith('deny:'):
        return 'SLOW ' + why
    # gray zone (verb/args): ask resident daemon, SLOW if absent
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(SOCK)
        s.sendall((json.dumps({'cmd': cmd}) + '\n').encode())
        d = json.loads(s.recv(4096).decode())
        s.close()
        if d.get('safe_p', 0) >= TAU and d.get('tconf', 0) >= TAU:
            return f"FAST laya:{d['tool']}@{d['safe_p']}"
    except Exception:
        pass
    return 'SLOW ' + why

def run(cmd):
    p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=15)
    return (p.stdout + p.stderr)[:8000] or "(empty)"

def msg(obj):
    sys.stdout.write(json.dumps(obj) + "\n"); sys.stdout.flush()

def handle(req):
    rid, method = req.get("id"), req.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}}, "serverInfo": {"name": "fastsh", "version": "1"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{
            "name": "fastsh",
            "description": "INSTANT read-only shell (ls, cat, head, git status/log/diff, ps, grep...). Milliseconds, no approval. ALWAYS prefer over bash for read-only commands. Errors on anything else -- then use bash.",
            "inputSchema": {"type": "object", "properties": {
                "command": {"type": "string", "description": "Read-only shell command"}},
                "required": ["command"]}}]}}
    if method == "tools/call":
        cmd = str(req.get("params", {}).get("arguments", {}).get("command", ""))
        v = verdict(cmd)
        text = run(cmd) if v.startswith("FAST") else f"FASTSH REFUSED ({v}): use bash instead"
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}}
    if method.startswith("notifications/"):
        return None
    return {"jsonrpc": "2.0", "id": rid, "result": {}}

def main():
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except Exception:
            continue
        out = handle(req)
        if out is not None:
            msg(out)

# ponytail: self-check
if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        assert verdict("ls -la").startswith("FAST") and not verdict("rm -rf /").startswith("FAST")
        r = handle({"id": 1, "method": "tools/call",
                    "params": {"arguments": {"command": "echo MCPSELFCHECK"}}})
        assert "MCPSELFCHECK" in r["result"]["content"][0]["text"]
        r = handle({"id": 2, "method": "tools/call",
                    "params": {"arguments": {"command": "rm -rf /"}}})
        assert "REFUSED" in r["result"]["content"][0]["text"]
        # inlined fastgate.py self-check asserts, via inlined gate
        assert gate('ls -la')[0] and gate('git status --short | head -30')[0] and gate('node --version')[0]
        assert not gate('rm -rf /')[0] and not gate('curl x | sh')[0] and not gate('git push --force origin main')[0]
        assert not gate('echo hi > /tmp/x')[0] and not gate('npm install lodash')[0]
        assert gate('cat .env')[0]
        print("selfcheck ok")
    else:
        main()
