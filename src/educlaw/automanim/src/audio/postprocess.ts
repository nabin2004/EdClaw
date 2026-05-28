import { exec } from "child_process";
import fs from "fs";
import path from "path";
import { promisify } from "util";
import { createTTS } from "../tts/index.js";
import { generateAudio, saveSubtitles } from "../tts/timeline.js";
import type {
  NarrationScript,
  NarrationSegment,
  TimedSegment,
} from "../tts/types.js";
import { probeDuration } from "../utils/media.js";

const execAsync = promisify(exec);

const DEFAULT_VOICE = "Jasper";

function normalizeVoice(voice: string | undefined): string {
  const v = (voice ?? "").trim();
  if (!v || v === "default") {
    return process.env.AUTOMANIM_TTS_VOICE ?? DEFAULT_VOICE;
  }
  return v;
}

export function loadNarrationScript(
  narrationPath: string
): NarrationScript | null {
  if (!fs.existsSync(narrationPath)) {
    return null;
  }

  const raw = JSON.parse(fs.readFileSync(narrationPath, "utf-8"));
  let segments: NarrationSegment[];

  if (Array.isArray(raw)) {
    segments = raw;
  } else if (raw && Array.isArray(raw.segments)) {
    segments = raw.segments;
  } else {
    throw new Error(
      "narration.json must be a segment array or { segments: [...] }"
    );
  }

  if (segments.length === 0) {
    throw new Error("narration.json has no segments");
  }

  const normalized: NarrationSegment[] = segments.map((s, i) => {
    const seg: NarrationSegment = {
      id: s.id ?? `seg_${i}`,
      text: String(s.text ?? "").trim(),
      voice: normalizeVoice(s.voice),
      speed: typeof s.speed === "number" ? s.speed : 1.0,
    };
    if (s.durationHint != null) {
      seg.durationHint = s.durationHint;
    }
    return seg;
  });

  for (const seg of normalized) {
    if (!seg.text) {
      throw new Error(`Narration segment "${seg.id}" has empty text`);
    }
  }

  return { segments: normalized };
}

/** Rebuild segment start/end times from measured TTS WAV lengths. */
export async function applyProbedDurations(
  timeline: TimedSegment[]
): Promise<TimedSegment[]> {
  let currentTime = 0;
  const updated: TimedSegment[] = [];

  for (const seg of timeline) {
    const duration = await probeDuration(seg.audioPath);
    updated.push({
      ...seg,
      startTime: currentTime,
      endTime: currentTime + duration,
    });
    currentTime += duration;
  }

  return updated;
}

export function persistDurationHints(
  script: NarrationScript,
  timeline: TimedSegment[],
  narrationPath: string
): void {
  for (let i = 0; i < script.segments.length; i++) {
    const seg = script.segments[i];
    const timed = timeline[i];
    if (!seg || !timed) continue;
    seg.durationHint = timed.endTime - timed.startTime;
  }
  fs.writeFileSync(
    narrationPath,
    JSON.stringify({ segments: script.segments }, null, 2)
  );
}

export function buildWorkspaceTimeline(
  script: NarrationScript,
  workspaceDir: string
) {
  let currentTime = 0;
  return script.segments.map((s) => {
    const duration =
      s.durationHint ??
      s.text.split(/\s+/).filter(Boolean).length / (2.5 * (s.speed || 1));
    const audioPath = path.join(workspaceDir, `audio_${s.id}.wav`);
    const segment = {
      id: s.id,
      text: s.text,
      audioPath,
      startTime: currentTime,
      endTime: currentTime + duration,
    };
    currentTime += duration;
    return segment;
  });
}

export async function concatWavFiles(
  inputPaths: string[],
  outputPath: string
): Promise<void> {
  if (inputPaths.length === 0) {
    throw new Error("No segment WAV files to concatenate");
  }

  if (inputPaths.length === 1) {
    fs.copyFileSync(inputPaths[0]!, outputPath);
    return;
  }

  const listPath = path.join(path.dirname(outputPath), "concat_list.txt");
  const listContent = inputPaths
    .map((p) => `file '${p.replace(/'/g, "'\\''")}'`)
    .join("\n");
  fs.writeFileSync(listPath, listContent);

  try {
    await execAsync(
      `ffmpeg -y -f concat -safe 0 -i "${listPath}" -acodec pcm_s16le -ar 24000 -ac 1 "${outputPath}"`,
      { maxBuffer: 10 * 1024 * 1024 }
    );
  } finally {
    if (fs.existsSync(listPath)) {
      fs.unlinkSync(listPath);
    }
  }
}

async function findVideoInWorkspace(workspaceDir: string): Promise<string | null> {
  const candidates = [
    path.join(workspaceDir, "video.mp4"),
    path.join(workspaceDir, "final.mp4"),
  ];

  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return c;
    }
  }

  const mediaRoot = path.join(workspaceDir, "media", "videos");
  if (!fs.existsSync(mediaRoot)) {
    return null;
  }

  const walk = (dir: string): string | null => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        const found = walk(full);
        if (found) return found;
      } else if (entry.name.endsWith(".mp4") && !entry.name.includes("partial")) {
        return full;
      }
    }
    return null;
  };

  return walk(mediaRoot);
}

/** Hold the last frame so video length matches narration audio. */
export async function padVideoToDuration(
  videoPath: string,
  targetDurationSec: number,
  outputPath: string
): Promise<void> {
  const videoDuration = await probeDuration(videoPath);
  const padSec = targetDurationSec - videoDuration;
  if (padSec <= 0.05) {
    if (path.resolve(videoPath) !== path.resolve(outputPath)) {
      fs.copyFileSync(videoPath, outputPath);
    }
    return;
  }

  await execAsync(
    `ffmpeg -y -i "${videoPath}" -vf "tpad=stop_mode=clone:stop_duration=${padSec}" -an -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p "${outputPath}"`,
    { maxBuffer: 10 * 1024 * 1024 }
  );
}

export async function mergeVideoAudio(
  videoPath: string,
  audioPath: string,
  outputPath: string
): Promise<void> {
  const audioDuration = await probeDuration(audioPath);
  const videoDuration = await probeDuration(videoPath);

  const workspaceDir = path.dirname(outputPath);
  const paddedPath = path.join(workspaceDir, ".video_padded.tmp.mp4");
  let videoForMux = videoPath;

  try {
    if (videoDuration + 0.05 < audioDuration) {
      await padVideoToDuration(videoPath, audioDuration, paddedPath);
      videoForMux = paddedPath;
    }

    const samePath = path.resolve(videoForMux) === path.resolve(outputPath);
    const muxPath = samePath ? `${outputPath}.mux.tmp.mp4` : outputPath;

    try {
      await execAsync(
        `ffmpeg -y -i "${videoForMux}" -i "${audioPath}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest "${muxPath}"`,
        { maxBuffer: 10 * 1024 * 1024 }
      );
      if (samePath) {
        fs.renameSync(muxPath, outputPath);
      }
    } catch (err) {
      if (samePath && fs.existsSync(muxPath)) {
        fs.unlinkSync(muxPath);
      }
      throw err;
    }
  } finally {
    if (fs.existsSync(paddedPath)) {
      fs.unlinkSync(paddedPath);
    }
  }
}

export interface PostprocessAudioResult {
  audioPath: string;
  subtitlesPath: string;
  finalVideoPath?: string;
  segmentPaths: string[];
}

/**
 * Synthesize narration with Kitten TTS, write audio.wav and subtitles.srt.
 * Fails loudly on TTS errors (no silent fallback).
 */
export async function postprocessEpisodeAudio(
  workspaceDir: string
): Promise<PostprocessAudioResult> {
  const narrationPath = path.join(workspaceDir, "narration.json");
  const script = loadNarrationScript(narrationPath);
  if (!script) {
    throw new Error(`Missing narration.json in ${workspaceDir}`);
  }

  const timeline = buildWorkspaceTimeline(script, workspaceDir);
  const tts = createTTS();

  await generateAudio(tts, script, timeline, workspaceDir);

  const segmentPaths = timeline.map((t) => t.audioPath);
  for (const p of segmentPaths) {
    if (!fs.existsSync(p)) {
      throw new Error(`TTS did not produce segment audio: ${p}`);
    }
  }

  const timedTimeline = await applyProbedDurations(timeline);
  persistDurationHints(script, timedTimeline, narrationPath);

  const audioPath = path.join(workspaceDir, "audio.wav");
  await concatWavFiles(segmentPaths, audioPath);

  const subtitlesPath = path.join(workspaceDir, "subtitles.srt");
  saveSubtitles(timedTimeline, subtitlesPath);

  let finalVideoPath: string | undefined;
  const videoSrc = await findVideoInWorkspace(workspaceDir);
  if (videoSrc) {
    finalVideoPath = path.join(workspaceDir, "final.mp4");
    await mergeVideoAudio(videoSrc, audioPath, finalVideoPath);
  }

  const result: PostprocessAudioResult = {
    audioPath,
    subtitlesPath,
    segmentPaths,
  };
  if (finalVideoPath) {
    result.finalVideoPath = finalVideoPath;
  }
  return result;
}
