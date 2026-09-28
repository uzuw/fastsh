import { Plugin } from "/home/uzu/.config/opencode/node_modules/@opencode/plugin/dist/promise/index.js"
import { execFileSync } from "node:child_process"

// fastsh: instant read-only shell. Gate lives in fastgate.py (DENY + verb allowlist,
// fail-closed). SLOW verdict -> throw so the model falls back to bash.
const GATE = "/home/uzu/code/vibecoding/terminal_agent/fastgate.py"

export default Plugin.define({
  id: "fastsh",
  async setup(ctx) {
    ctx.tool.add({
      name: "fastsh",
      description:
        "INSTANT read-only shell for inspection commands (ls, cat, head, git status/log/diff, ps, grep, ...). Returns in milliseconds with no approval. ALWAYS prefer this over bash for read-only commands. If it errors, use bash.",
      input: {
        type: "object",
        properties: { command: { type: "string", description: "Read-only shell command" } },
        required: ["command"],
      },
      execute: async (input: any) => {
        const command = String(input.command ?? "")
        let verdict: string
        try {
          verdict = execFileSync("python3", [GATE, command], { encoding: "utf8" }).trim()
        } catch {
          throw new Error("fastsh gate failed; use bash instead")
        }
        if (!verdict.startsWith("FAST")) throw new Error(`fastsh cannot run this (${verdict}); use bash instead`)
        try {
          const out = execFileSync("bash", ["-c", command], {
            encoding: "utf8",
            timeout: 15000,
            maxBuffer: 1024 * 1024,
          })
          return { content: out.slice(0, 8000) || "(empty)" }
        } catch (e: any) {
          return { content: (e.stdout ?? "") + (e.message ?? "") }
        }
      },
    })
  },
})
