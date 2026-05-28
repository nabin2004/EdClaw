import fs from "fs";
import path from "path";

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

/**
 * Validate episode outputs
 */
export function validateEpisodeOutputs(episodeDir: string): ValidationResult {
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

  // Validate narration.json if it exists
  const narrationPath = path.join(episodeDir, "narration.json");
  if (fs.existsSync(narrationPath)) {
    const narrationResult = validateJsonFile(narrationPath, ["segments"]);
    result.valid = result.valid && narrationResult.valid;
    result.errors.push(...narrationResult.errors);
  }

  return result;
}
