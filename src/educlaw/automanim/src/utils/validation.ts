import { exec } from "child_process";
import fs from "fs";
import path from "path";
import { promisify } from "util";
import { probeDuration } from "./media.js";

const execAsync = promisify(exec);

const SYNC_TOLERANCE_SEC = 0.75;

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Validate that a file exists and is non-empty
 */
export function validateFileExists(
  filePath: string,
  required: boolean = true
): ValidationResult {
  const result: ValidationResult = { valid: true, errors: [], warnings: [] };

  if (!fs.existsSync(filePath)) {
    if (required) {
      result.valid = false;
      result.errors.push(`Required file missing: ${filePath}`);
    } else {
      result.warnings.push(`Optional file missing: ${filePath}`);
    }
    return result;
  }

  const stats = fs.statSync(filePath);
  if (stats.size === 0) {
    result.valid = false;
    result.errors.push(`File is empty: ${filePath}`);
  }

  return result;
}

/**
 * Validate video file has reasonable size
 */
export function validateVideoFile(filePath: string): ValidationResult {
  const result = validateFileExists(filePath, true);
  if (!result.valid) return result;

  const stats = fs.statSync(filePath);
  const sizeMB = stats.size / (1024 * 1024);

  if (sizeMB < 0.01) {
    result.valid = false;
    result.errors.push(`Video file too small (${sizeMB.toFixed(2)}MB): ${filePath}`);
  } else if (sizeMB > 500) {
    result.warnings.push(`Video file very large (${sizeMB.toFixed(2)}MB): ${filePath}`);
  }

  return result;
}

/**
 * Validate JSON file structure
 */
export function validateJsonFile(filePath: string, expectedKeys: string[] = []): ValidationResult {
  const result = validateFileExists(filePath, true);
  if (!result.valid) return result;

  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const data = JSON.parse(content);

    for (const key of expectedKeys) {
      if (!(key in data)) {
        result.valid = false;
        result.errors.push(`Missing required key "${key}" in ${filePath}`);
      }
    }
  } catch (error) {
    result.valid = false;
    result.errors.push(`Invalid JSON in ${filePath}: ${(error as Error).message}`);
  }

  return result;
}

function validateNarrationJson(filePath: string): ValidationResult {
  const result = validateFileExists(filePath, false);
  if (!fs.existsSync(filePath)) {
    return result;
  }

  try {
    const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const segments = Array.isArray(data)
      ? data
      : data?.segments;
    if (!Array.isArray(segments) || segments.length === 0) {
      result.valid = false;
      result.errors.push(
        `narration.json must be a non-empty segment array or { "segments": [...] }: ${filePath}`
      );
    }
  } catch (error) {
    result.valid = false;
    result.errors.push(`Invalid JSON in ${filePath}: ${(error as Error).message}`);
  }

  return result;
}

/**
 * Fail if audio.wav appears to be silent (peak near zero).
 */
export async function validateAudioNotSilent(
  filePath: string
): Promise<ValidationResult> {
  const result = validateFileExists(filePath, false);
  if (!fs.existsSync(filePath)) {
    return result;
  }

  try {
    const { stdout, stderr } = await execAsync(
      `ffmpeg -i "${filePath}" -af volumedetect -f null - 2>&1`,
      { maxBuffer: 2 * 1024 * 1024 }
    );
    const output = `${stdout}\n${stderr}`;
    const peakMatch = output.match(/max_volume:\s*([-\d.]+)\s*dB/);
    if (peakMatch) {
      const peakDb = parseFloat(peakMatch[1]!);
      if (peakDb <= -60) {
        result.valid = false;
        result.errors.push(
          `audio.wav appears silent (max_volume ${peakDb} dB): ${filePath}`
        );
      }
    }
  } catch {
    result.warnings.push(
      `Could not run volumedetect on audio.wav: ${filePath}`
    );
  }

  return result;
}

/**
 * Fail when muxed video length does not match narration audio.
 */
export async function validateVideoAudioSync(
  videoPath: string,
  audioPath: string
): Promise<ValidationResult> {
  const result: ValidationResult = { valid: true, errors: [], warnings: [] };

  if (!fs.existsSync(videoPath) || !fs.existsSync(audioPath)) {
    return result;
  }

  try {
    const videoDur = await probeDuration(videoPath);
    const audioDur = await probeDuration(audioPath);
    const drift = Math.abs(videoDur - audioDur);

    if (drift > SYNC_TOLERANCE_SEC) {
      result.valid = false;
      result.errors.push(
        `video (${videoDur.toFixed(2)}s) and audio (${audioDur.toFixed(2)}s) are out of sync by ${drift.toFixed(2)}s`
      );
    }
  } catch (error) {
    result.warnings.push(
      `Could not compare video/audio duration: ${(error as Error).message}`
    );
  }

  return result;
}

/**
 * Validate episode outputs
 */
export async function validateEpisodeOutputs(
  episodeDir: string
): Promise<ValidationResult> {
  const result: ValidationResult = { valid: true, errors: [], warnings: [] };

  // Required files
  const requiredFiles = [
    { path: "scene.py", validator: validateFileExists },
    { path: "video.mp4", validator: validateVideoFile },
  ];

  for (const { path: file, validator } of requiredFiles) {
    const filePath = path.join(episodeDir, file);
    const fileResult = validator(filePath);
    result.valid = result.valid && fileResult.valid;
    result.errors.push(...fileResult.errors);
    result.warnings.push(...fileResult.warnings);
  }

  // Optional files
  const optionalFiles = ["narration.json", "audio.wav", "subtitles.srt", "metadata.json"];
  for (const file of optionalFiles) {
    const filePath = path.join(episodeDir, file);
    const fileResult = validateFileExists(filePath, false);
    result.warnings.push(...fileResult.warnings);
  }

  const narrationPath = path.join(episodeDir, "narration.json");
  const narrationResult = validateNarrationJson(narrationPath);
  result.valid = result.valid && narrationResult.valid;
  result.errors.push(...narrationResult.errors);

  const audioPath = path.join(episodeDir, "audio.wav");
  const audioResult = await validateAudioNotSilent(audioPath);
  result.valid = result.valid && audioResult.valid;
  result.errors.push(...audioResult.errors);
  result.warnings.push(...audioResult.warnings);

  const videoPath = path.join(episodeDir, "video.mp4");
  const syncResult = await validateVideoAudioSync(videoPath, audioPath);
  result.valid = result.valid && syncResult.valid;
  result.errors.push(...syncResult.errors);
  result.warnings.push(...syncResult.warnings);

  return result;
}
