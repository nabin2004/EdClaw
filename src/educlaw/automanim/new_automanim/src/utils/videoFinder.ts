import fs from "fs";
import path from "path";

export function findVideos(
  dir: string
): string[] {
  const results: string[] = [];

  function walk(current: string) {
    const entries = fs.readdirSync(current);

    for (const entry of entries) {
      const full = path.join(current, entry);

      const stat = fs.statSync(full);

      if (stat.isDirectory()) {
        walk(full);
      } else if (full.endsWith(".mp4")) {
        results.push(full);
      }
    }
  }

  walk(dir);

  return results;
}