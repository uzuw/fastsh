#!/bin/bash
cd /home/uzu/code/vibecoding/terminal_agent
TASKS=("node --version" "pwd" "ls .opencode/memory" "git status --short | head -5" "grep -c Laya README.md")
run_arm() {
  local tag="$1"
  mkdir -p baseline/logs_mcp_$tag
  > baseline/results_mcp_$tag.jsonl
  local i=0
  for t in "${TASKS[@]}"; do
    i=$((i+1))
    local s e dt
    s=$(date +%s.%N)
    timeout 100 opencode run --standalone --auto "Run this shell command and report the exact output: $t" 2>&1 | tail -n 3 > "baseline/logs_mcp_$tag/t$(printf %02d $i).log"
    e=$(date +%s.%N); dt=$(echo "$e - $s" | bc)
    printf '{"task":%d,"secs":%.2f}\n' "$i" "$dt" >> baseline/results_mcp_$tag.jsonl
    echo "[$tag] task $i: ${dt}s"
  done
}
run_arm "$1"
