#!/bin/bash
# 20-task shell baseline: each task forces real shell use. ponytail: one file, tasks inline.
cd /home/uzu/code/vibecoding/terminal_agent
mkdir -p baseline/logs_fast
> baseline/results_fast.jsonl
sleep 600 & SLEEP_PID=$!
echo "decoy sleep pid: $SLEEP_PID"

i=0
run() {
  i=$((i+1)); local prompt="$1"
  local start end dt out
  start=$(date +%s.%N)
  out=$(timeout 100 opencode run --standalone --auto "$prompt" 2>&1 | tail -n 5)
  end=$(date +%s.%N)
  dt=$(echo "$end - $start" | bc)
  printf '%s\n' "$out" > "baseline/logs_fast/t$(printf %02d $i).log"
  printf '{"task":%d,"secs":%.2f}\n' "$i" "$dt" >> baseline/results_fast.jsonl
  echo "task $i: ${dt}s"
}

run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: node --version"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: python3 --version"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: pwd"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: wc -l README.md"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: du -sh ."
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: whoami"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: uname -a"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: date +%Y-%m-%d"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: ls .opencode/memory"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: find . -maxdepth 2 -name '*.md'"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: grep -c Laya README.md"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: stat -c %s README.md"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: echo hello-baseline"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: head -n 3 README.md"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: ps -p $SLEEP_PID -o pid=,comm="
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: df -h . | tail -n 1"
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: env | grep -c ^HOME="
run "Using the shell \(fastsh cannot run kill, use bash\), kill process $SLEEP_PID and then confirm it is gone. Report what you did."
run "Prefer the fastsh tool for any read-only shell command. Run this shell command and report the exact output: kill -0 $SLEEP_PID && echo alive || echo gone"
kill -9 $SLEEP_PID 2>/dev/null
echo DONE
python3 -c "
import json
ts=[json.loads(l)['secs'] for l in open('baseline/results_fast.jsonl')]
ts.sort()
import statistics
n=len(ts)
p50=ts[n//2]; p95=ts[int(n*0.95)-1] if n>1 else ts[0]
print(f'n={n} min={ts[0]:.1f}s p50={p50:.1f}s p95={p95:.1f}s max={ts[-1]:.1f}s mean={statistics.mean(ts):.1f}s total={sum(ts):.0f}s')
"
