import fs from "fs";
import path from "path";
import {
  AuthStorage,
  createAgentSession,
  ModelRegistry,
  SessionManager,
} from "@earendil-works/pi-coding-agent";
import { getModel } from "@earendil-works/pi-ai";
import { createTools } from "./tools/index.js";

export interface EpisodeMetadata {
  episode_id: string;
  prompt: string;
  model: string;
  generated_code?: string;
  narration_segments?: any[];
  tool_logs: any[];
  status: "success" | "failure";
  render_duration_ms: number;
  timestamp: string;
  error?: string;
  seed?: number;
}

export interface PipelineOptions {
  modelName: string;
  provider: string;
  maxRetries: number;
  seed?: number;
}

export async function generateEpisode(
  episodeId: string,
  userPrompt: string,
  outputBaseDir: string,
  options: PipelineOptions
): Promise<EpisodeMetadata> {
  const startTime = Date.now();
  const episodeDir = path.join(outputBaseDir, episodeId);
  const workspaceDir = path.join(process.cwd(), `workspace_${episodeId}`);

  // Ensure directories exist
  if (!fs.existsSync(episodeDir)) fs.mkdirSync(episodeDir, { recursive: true });
  if (!fs.existsSync(workspaceDir)) fs.mkdirSync(workspaceDir, { recursive: true });

  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);
  const model = getModel(options.provider, options.modelName);

  if (!model) {
    throw new Error(`Model ${options.modelName} not found for provider ${options.provider}`);
  }

  const { session } = await createAgentSession({
    cwd: workspaceDir,
    sessionManager: SessionManager.create(workspaceDir),
    authStorage,
    modelRegistry,
    model,
    thinkingLevel: "medium",
    tools: ["read", "write", "edit", "safe_bash"],
    customTools: createTools(workspaceDir),
  });

  const toolLogs: any[] = [];
  session.subscribe((event) => {
    if (event.type === "tool_execution_start" || event.type === "tool_execution_end") {
      toolLogs.push(event);
    }
  });

  const instructionPrompt = `
Create a Manim Community Edition animation.

USER REQUEST:
${userPrompt}

Requirements:
- Write code to scene.py
- Scene class name must be AutoScene
- Use modern Manim CE APIs only
- Keep animation under 30 seconds
- Render using: manim -pql scene.py AutoScene
- Extract narration into narration.json (array of {id, text, voice, speed})
- Generate audio.wav using the generate_tts tool (you can generate it for the entire narration or per segment and merge using ffmpeg)
- Finally, produce final.mp4 (merged video and audio using ffmpeg: ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4)

If rendering fails:
- analyze the error
- fix the code
- rerun the render (Max 3 attempts)

Output Files Expected in workspace:
- scene.py
- narration.json
- final.mp4
`;

  let status: "success" | "failure" = "failure";
  let errorMsg = "";

  try {
    await session.prompt(instructionPrompt);
    status = "success";
  } catch (err: any) {
    status = "failure";
    errorMsg = err.message;
  }

  const endTime = Date.now();
  const renderDuration = endTime - startTime;

  // Collect artifacts
  const artifacts = ["scene.py", "narration.json", "audio.wav", "subtitles.srt", "final.mp4"];
  for (const file of artifacts) {
    const srcPath = path.join(workspaceDir, file);
    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, path.join(episodeDir, file));
    }
  }

  // Final video should be renamed to video.mp4 for consistency
  if (fs.existsSync(path.join(episodeDir, "final.mp4"))) {
    fs.renameSync(path.join(episodeDir, "final.mp4"), path.join(episodeDir, "video.mp4"));
  }

  // Read generated code and narration for metadata
  let generatedCode = "";
  if (fs.existsSync(path.join(episodeDir, "scene.py"))) {
    generatedCode = fs.readFileSync(path.join(episodeDir, "scene.py"), "utf-8");
  }

  let narrationSegments = [];
  if (fs.existsSync(path.join(episodeDir, "narration.json"))) {
    try {
      narrationSegments = JSON.parse(fs.readFileSync(path.join(episodeDir, "narration.json"), "utf-8"));
    } catch (e) {}
  }

  const metadata: EpisodeMetadata = {
    episode_id: episodeId,
    prompt: userPrompt,
    model: options.modelName,
    generated_code: generatedCode,
    narration_segments: narrationSegments,
    tool_logs: toolLogs,
    status,
    render_duration_ms: renderDuration,
    timestamp: new Date().toISOString(),
    error: errorMsg || undefined,
    seed: options.seed,
  };

  fs.writeFileSync(path.join(episodeDir, "metadata.json"), JSON.stringify(metadata, null, 2));

  // Cleanup workspace
  // fs.rmSync(workspaceDir, { recursive: true, force: true });

  return metadata;
}
