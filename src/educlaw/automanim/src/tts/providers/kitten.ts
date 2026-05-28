import { spawn } from "child_process";
import fs from "fs";
import os from "os";
import path from "path";
import { fileURLToPath } from "url";
import type { TTSProvider, TTSRequest, TTSResult } from "../types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const DEFAULT_MODEL_ID = "KittenML/kitten-tts-nano-0.8-int8";
const DEFAULT_VOICE = "Jasper";

function resolvePython(): string {
  return process.env.AUTOMANIM_PYTHON ?? "python3";
}

function normalizeVoice(voice: string | undefined): string {
  const v = (voice ?? "").trim();
  if (!v || v === "default") {
    return process.env.AUTOMANIM_TTS_VOICE ?? DEFAULT_VOICE;
  }
  return v;
}

export class KittenTTSProvider implements TTSProvider {
  name = "kitten";

  async synthesize(req: TTSRequest): Promise<TTSResult> {
    const scriptPath = path.join(__dirname, "kitten_runner.py");
    const outputPath = path.resolve(req.outputPath);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });

    const voice = normalizeVoice(req.voice);
    const env = {
      ...process.env,
      AUTOMANIM_TTS_MODEL_ID:
        process.env.AUTOMANIM_TTS_MODEL_ID ?? DEFAULT_MODEL_ID,
      AUTOMANIM_TTS_CACHE_DIR:
        process.env.AUTOMANIM_TTS_CACHE_DIR ??
        path.join(os.homedir(), ".educlaw", "tts"),
    };

    return new Promise((resolve) => {
      const args = [
        scriptPath,
        req.text,
        outputPath,
        voice,
        String(req.speed ?? 1.0),
      ];

      const child = spawn(resolvePython(), args, { env });

      let stderr = "";

      child.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      child.on("error", (err) => {
        resolve({
          success: false,
          error: err.message,
        });
      });

      child.on("close", (code) => {
        if (code === 0 && fs.existsSync(outputPath)) {
          resolve({
            success: true,
            outputPath,
          });
        } else {
          resolve({
            success: false,
            error: stderr || `kitten_runner exited with code ${code}`,
          });
        }
      });
    });
  }

  async synthesizeSegment(
    segment: import("../types.js").NarrationSegment,
    outputPath: string
  ): Promise<TTSResult> {
    return this.synthesize({
      text: segment.text,
      outputPath,
      voice: segment.voice,
      speed: segment.speed,
    });
  }
}
