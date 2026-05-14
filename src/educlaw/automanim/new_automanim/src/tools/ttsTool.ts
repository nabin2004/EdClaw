import { Type } from "typebox";
import { defineTool } from "@earendil-works/pi-coding-agent";
import { createTTS } from "../tts/index.js";
import path from "path";

export const createTtsTool = (cwd: string) => defineTool({
  name: "generate_tts",
  label: "Generate TTS",
  description: "Generate audio from text using KittenTTS",
  parameters: Type.Object({
    text: Type.String(),
    outputPath: Type.String(),
    voice: Type.Optional(Type.String()),
    speed: Type.Optional(Type.Number()),
  }),
  execute: async (_id, params) => {
    const tts = createTTS();
    const provider = tts.get("kitten");
    
    // Resolve output path relative to workspace if not absolute
    const fullOutputPath = path.isAbsolute(params.outputPath) 
      ? params.outputPath 
      : path.join(cwd, params.outputPath);
    
    try {
      const result = await provider.synthesize({
        text: params.text,
        outputPath: fullOutputPath,
        voice: params.voice,
        speed: params.speed,
      });

      if (result.success) {
        return {
          content: [
            {
              type: "text",
              text: `Audio generated successfully at ${params.outputPath}`,
            },
          ],
          details: {},
        };
      } else {
        return {
          content: [
            {
              type: "text",
              text: `Failed to generate audio: ${result.error}`,
            },
          ],
          details: {},
        };
      }
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
