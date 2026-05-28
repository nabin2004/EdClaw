import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/** Duration in seconds from ffprobe. */
export async function probeDuration(filePath: string): Promise<number> {
  const { stdout } = await execAsync(
    `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${filePath}"`,
    { maxBuffer: 1024 * 1024 }
  );
  const duration = parseFloat(stdout.trim());
  if (!Number.isFinite(duration) || duration <= 0) {
    throw new Error(`Could not probe media duration: ${filePath}`);
  }
  return duration;
}
