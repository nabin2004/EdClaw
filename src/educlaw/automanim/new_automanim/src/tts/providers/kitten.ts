import { spawn } from "child_process";
import path from "path";
import type { TTSProvider, TTSRequest, TTSResult } from "../types.js";

export class KittenTTSProvider implements TTSProvider {
  name = "kitten";

  async synthesize(req: TTSRequest): Promise<TTSResult> {
    return new Promise((resolve) => {
      const scriptPath = path.resolve(
        "src/tts/providers/kitten_runner.py"
      );

      const args = [
        scriptPath,
        req.text,
        req.outputPath,
        req.voice ?? "Jasper",
        String(req.speed ?? 1.0),
      ];

      const process = spawn("python", args);

      let stderr = "";

      process.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      process.on("close", (code) => {
        if (code === 0) {
          resolve({
            success: true,
            outputPath: req.outputPath,
          });
        } else {
          resolve({
            success: false,
            error: stderr,
          });
        }
      });
    });
  }

  async synthesizeSegment(segment: import("../types.js").NarrationSegment, outputPath: string): Promise<TTSResult> {
    return this.synthesize({
      text: segment.text,
      outputPath,
      voice: segment.voice,
      speed: segment.speed,
    });
  }
}