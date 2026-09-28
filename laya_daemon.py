#!/usr/bin/env python3
"""Resident Laya gate daemon. Loads laya-cli-best once, serves ms verdicts over a unix socket.
Protocol (JSON lines): {"cmd": "..."} -> {"tool":..,"tconf":..,"safe_p":..,"ms":..}
ponytail: stdlib + laya only, no framework."""
import json, os, socket, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
LAYA_VENV = os.environ.get('LAYA_VENV', '/home/uzu/code/infra/laya/.venv/lib/python3.14/site-packages')
LAYA_MODEL = os.environ.get('LAYA_MODEL', '/home/uzu/code/infra/laya/laya-cli-best')
sys.path.insert(0, LAYA_VENV)
SOCK = os.environ.get('LAYA_SOCK', '/tmp/laya-gate.sock')
Q = {'tool': {'type': 'choice', 'instructions': 'Which tool owns this command?',
              'criteria': {'git': 'git version control', 'docker': 'docker containers',
                           'node': 'npm/node javascript', 'k8s': 'kubectl kubernetes',
                           'shell': 'shell/system commands'}},
     'safe': {'type': 'noul', 'instructions': 'Is this command safe to run without human review?'}}

agent = None

def load():
    global agent
    from laya import Agent
    t = time.time()
    agent = Agent(LAYA_MODEL)
    print(f'laya daemon: model loaded in {(time.time()-t)*1000:.0f}ms', flush=True)

def verdict(cmd):
    t = time.time()
    ans = agent.system_one({'cmd': cmd}, Q)['answers']
    return {'tool': ans['tool'].get('choice'), 'tconf': round(ans['tool'].get('confidence', 0), 3),
            'safe_p': round(float(ans['safe'].get('noul', 0)), 3),
            'ms': round((time.time() - t) * 1000, 1)}

def serve():
    if os.path.exists(SOCK):
        os.remove(SOCK)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK)
    s.listen(50)
    print('laya daemon: serving ' + SOCK, flush=True)
    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()

def handle(conn):
    try:
        data = conn.recv(4096).decode()
        cmd = json.loads(data).get('cmd', '')
        conn.sendall((json.dumps(verdict(cmd)) + '\n').encode())
    except Exception as e:
        try:
            conn.sendall((json.dumps({'error': str(e)}) + '\n').encode())
        except Exception:
            pass
    finally:
        conn.close()

if __name__ == '__main__':
    load()
    serve()
