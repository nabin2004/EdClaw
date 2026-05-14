import type { TTSProvider } from "./types.js";

export class TTSRegistry {
  private providers = new Map<string, TTSProvider>();

  register(provider: TTSProvider) {
    this.providers.set(provider.name, provider);
  }

  get(name: string): TTSProvider {
    const p = this.providers.get(name);

    if (!p) {
      throw new Error(
        `TTS provider not found: ${name}`
      );
    }

    return p;
  }

  list() {
    return [...this.providers.keys()];
  }
}