import fs from "fs";
import path from "path";
import { generateEpisode } from "./pipeline.js";
import type { EpisodeMetadata } from "./pipeline.js";

async function main() {
  const args = process.argv.slice(2);
  const getArg = (name: string) => {
    const idx = args.indexOf(name);
    return idx !== -1 ? args[idx + 1] : null;
  };

  const episodesCount = parseInt(getArg("--episodes") || "1");
  const concurrency = parseInt(getArg("--concurrency") || "1");
  const outputDir = getArg("--output") || "./dataset";
  const promptsFile = getArg("--prompts");
  const resume = args.includes("--resume");
  const timeoutMs = parseInt(getArg("--timeout") || "600000"); // 10 minutes default
  const enableCircuitBreaker = args.includes("--circuit-breaker");

  console.log(`Starting data generation factory...`);
  console.log(`Episodes: ${episodesCount}`);
  console.log(`Concurrency: ${concurrency}`);
  console.log(`Output: ${outputDir}`);
  console.log(`Timeout: ${timeoutMs}ms`);
  console.log(`Circuit Breaker: ${enableCircuitBreaker ? "enabled" : "disabled"}`);

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  let prompts: string[] = [];
  if (promptsFile && fs.existsSync(promptsFile)) {
    prompts = fs.readFileSync(promptsFile, "utf-8").split("\n").filter(l => l.trim().length > 0);
  } else {
    // Default prompt if none provided
    prompts = Array(episodesCount).fill("Create a basic math animation about fractions.");
  }

  if (prompts.length === 0) {
    prompts = Array(episodesCount).fill("Create a basic math animation about fractions.");
  }

  let startIdx = 1;
  if (resume) {
    const existing = fs.readdirSync(outputDir).filter(f => f.startsWith("episode_")).length;
    startIdx = existing + 1;
    console.log(`Resuming from episode ${startIdx}`);
  }

  const results: EpisodeMetadata[] = [];
  const queue = [...Array(episodesCount).keys()].map(i => i + startIdx);

  const workers = Array(concurrency).fill(null).map(async () => {
    while (queue.length > 0) {
      const i = queue.shift()!;
      const episodeId = `episode_${String(i).padStart(4, "0")}`;
      const prompt = prompts[(i - 1) % prompts.length] || "Create a basic math animation about fractions.";

      console.log(`[${episodeId}] Starting...`);
      try {
        const metadata = await generateEpisode(episodeId, prompt, outputDir, {
          modelName: "moonshotai/kimi-k2.5",
          provider: "openrouter",
          maxRetries: 3,
          timeoutMs,
          enableCircuitBreaker,
        });
        results.push(metadata);
        console.log(`[${episodeId}] Finished with status: ${metadata.status}`);
      } catch (err) {
        console.error(`[${episodeId}] Fatal error:`, err);
      }
    }
  });

  await Promise.all(workers);

  const report = {
    total_episodes: results.length,
    success_count: results.filter(r => r.status === "success").length,
    failure_count: results.filter(r => r.status === "failure").length,
    average_duration_ms: results.reduce((acc, r) => acc + r.render_duration_ms, 0) / results.length,
    episodes: results.map(r => ({ id: r.episode_id, status: r.status })),
  };

  fs.writeFileSync(path.join(outputDir, "run_report.json"), JSON.stringify(report, null, 2));
  console.log(`\nBatch completed. Report saved to ${path.join(outputDir, "run_report.json")}`);
}

main().catch(err => {
  console.error("Batch job failed:", err);
  process.exit(1);
});
