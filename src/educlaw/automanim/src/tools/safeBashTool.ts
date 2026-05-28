import { Type } from "typebox";
import { defineTool } from "@earendil-works/pi-coding-agent";
import { safeExecute } from "../utils/safeBash.js";

export const createSafeBashTool = (cwd: string) => defineTool({
  name: "safe_bash",
  label: "Safe Bash",
  description: "Execute restricted shell commands safely (manim, python, ffmpeg, etc.)",
  parameters: Type.Object({
    command: Type.String(),
  }),
  execute: async (_id, params) => {
    try {
      const result = await safeExecute(params.command, cwd);
      return {
        content: [
          {
            type: "text",
            text: result.stdout || "Command completed",
          },
        ],
        details: {
          stderr: result.stderr,
        },
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: String(error),
          },
        ],
        details: {},
      };
    }
  },
});
