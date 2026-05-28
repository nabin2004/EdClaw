import { TTSRegistry } from "./registry.js";
import { KittenTTSProvider } from "./providers/kitten.js";

export function createTTS() {
  const registry = new TTSRegistry();
  registry.register(new KittenTTSProvider());
  return registry;
}

export * from "./types.js";
export * from "./registry.js";
export * from "./timeline.js";