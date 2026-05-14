// @ts-ignore
import readlineSync from "readline-sync";
import path from "path";
import fs from "fs";

import {
  AuthStorage,
  createAgentSession,
  ModelRegistry,
  SessionManager,
} from "@earendil-works/pi-coding-agent";
import { getModel } from "@earendil-works/pi-ai";
import { createTools } from "./tools/index.js";

const WORKSPACE_DIR = "./workspace";

// Ensure workspace exists
if (!fs.existsSync(WORKSPACE_DIR)) {
  fs.mkdirSync(WORKSPACE_DIR, { recursive: true });
}

const model = getModel(
  "openrouter",
);

if (!model) {
  throw new Error("Model not found. Ensure OpenRouter is configured.");
}

async function main() {
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);

  const { session } = await createAgentSession({
    cwd: WORKSPACE_DIR,
    sessionManager: SessionManager.create(WORKSPACE_DIR),
    authStorage,
    modelRegistry,
    model,
    thinkingLevel: "medium",
    tools: ["read", "write", "edit", "safe_bash"],
    customTools: createTools(WORKSPACE_DIR),
  });

  session.subscribe((event) => {
    switch (event.type) {
      case "agent_start":
        console.log("\n[agent started]");
        break;

      case "tool_execution_start":
        console.log(`\n[tool] ${event.toolName}`);
        break;

      case "tool_execution_end":
        console.log(
          `[tool finished] ${event.isError ? "ERROR" : "SUCCESS"
          }`
        );
        break;

      case "message_update":
        if (
          event.assistantMessageEvent.type ===
          "text_delta"
        ) {
          process.stdout.write(
            event.assistantMessageEvent.delta
          );
        }
        break;

      case "agent_end":
        console.log("\n\n[agent finished]");
        break;
    }
  });

  while (true) {
    const idea = readlineSync.question(
      "\nAnimation idea ('exit' to quit): "
    );

    if (idea === "exit") {
      break;
    }

    const prompt = `
Create a Manim Community Edition animation.

USER REQUEST:
${idea}

Requirements:
- Write code to scene.py
- Scene class name must be AutoScene
- Use modern Manim CE APIs only
- Keep code clean and readable
- Keep animation under 30 seconds
- Render using:
  manim -pql scene.py AutoScene

If rendering fails:
- analyze the error
- fix the code
- rerun the render

After rendering scene.py:
1. Extract narration into a NarrationScript with NarrationSegments (id, text, voice, speed).
2. Use timeline builder to map segments to a TimedSegment timeline.
3. Generate segmented audio for each segment in the timeline using Kitten TTS.
4. Merge segment audios into a single audio.wav if needed, or process them individually.
5. Generate and save subtitles.srt using the timeline.
6. Use ffmpeg to merge video and audio:
   ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4
`;

    await session.prompt(prompt);
  }
}

main().catch(err => {
  console.error("CLI failed:", err);
  process.exit(1);
});