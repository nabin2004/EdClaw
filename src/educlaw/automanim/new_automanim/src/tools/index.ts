import { createSafeBashTool } from "./safeBashTool.js";
import { createTtsTool } from "./ttsTool.js";

export const createTools = (cwd: string) => [
  createSafeBashTool(cwd),
  createTtsTool(cwd),
];

export const toolNames = ["read", "write", "edit", "safe_bash", "generate_tts"];
