import fs from "fs";
import path from "path";
import type { NarrationScript, TimedSegment, NarrationSegment } from "./types.js";
import { TTSRegistry } from "./registry.js";

export function estimateDuration(text: string, speed = 1) {
  const words = text.split(" ").length;
  const wordsPerSecond = 2.5 * speed;
  return words / wordsPerSecond;
}

export function buildTimeline(script: NarrationScript): TimedSegment[] {
  let currentTime = 0;

  return script.segments.map((s: NarrationSegment) => {
    const duration = s.durationHint ?? estimateDuration(s.text, s.speed);

    const segment: TimedSegment = {
      id: s.id,
      text: s.text,
      audioPath: `./workspace/audio_${s.id}.wav`,
      startTime: currentTime,
      endTime: currentTime + duration,
    };

    currentTime += duration;
    return segment;
  });
}

export async function generateAudio(
  tts: TTSRegistry,
  script: NarrationScript,
  timeline: TimedSegment[]
) {
  const provider = tts.get("kitten");

  for (let i = 0; i < script.segments.length; i++) {
    const seg = script.segments[i];
    const t = timeline[i];

    if (!seg || !t) continue;

    if (provider.synthesizeSegment) {
      await provider.synthesizeSegment(seg, t.audioPath);
    } else {
      await provider.synthesize({
        text: seg.text,
        voice: seg.voice,
        speed: seg.speed,
        outputPath: t.audioPath,
      });
    }
  }
}

export function generateSRT(timeline: TimedSegment[]): string {
  let srt = "";

  const formatTime = (t: number) => {
    // Math.floor to ensure we pass an integer to the Date constructor to avoid issues
    // Actually, t is in seconds.
    const msTime = Math.floor(t * 1000);
    const date = new Date(msTime);

    const hh = String(date.getUTCHours()).padStart(2, "0");
    const mm = String(date.getUTCMinutes()).padStart(2, "0");
    const ss = String(date.getUTCSeconds()).padStart(2, "0");
    const ms = String(date.getUTCMilliseconds()).padStart(3, "0");

    return `${hh}:${mm}:${ss},${ms}`;
  };

  timeline.forEach((seg, i) => {
    srt += `${i + 1}\n`;
    srt += `${formatTime(seg.startTime)} --> ${formatTime(seg.endTime)}\n`;
    srt += `${seg.text}\n\n`;
  });

  return srt;
}

export function saveSubtitles(timeline: TimedSegment[], outputPath = "./workspace/subtitles.srt") {
  const srtContent = generateSRT(timeline);
  fs.writeFileSync(outputPath, srtContent);
}
