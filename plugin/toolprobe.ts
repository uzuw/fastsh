import { Plugin } from "/home/uzu/.config/opencode/node_modules/@opencode/plugin/dist/promise/index.js"

// probe: log tool ids + description sizes, optionally strip to allowlist via STRIP=1
const KEEP = ["shell", "read", "fastsh", "fastsh_fastsh"]

export default Plugin.define({
  id: "toolprobe",
  async setup(ctx) {
    await ctx.tool.transform((editor) => {
      const all = editor.list()
      const total = all.reduce((n, t) => n + (t.description?.length ?? 0), 0)
      console.warn(`[toolprobe] tools=${all.length} descChars=${total}`)
      console.warn(`[toolprobe] ids=` + all.map((t) => t.id).join(","))
      if (process.env.STRIP === "1") {
        for (const t of all) if (!KEEP.includes(t.id)) editor.remove(t.id)
        console.warn(`[toolprobe] stripped to ` + editor.list().map((t) => t.id).join(","))
      }
    })
  },
})
