export type TTSRequest = {
  text: string;
  outputPath: string;
  voice?: string;
  speed?: number;
};

export type TTSResult = {
  success: boolean;
  outputPath?: string;
  error?: string;
};

export type NarrationSegment = {
  id: string;
  text: string;
  voice: string;
  speed: number;
  durationHint?: number;
};

export type NarrationScript = {
  segments: NarrationSegment[];
};

export type TimedSegment = {
  id: string;
  text: string;
  audioPath: string;
  startTime: number;
  endTime: number;
};

export type TTSProvider = {
  name: string;
  synthesize(req: TTSRequest): Promise<TTSResult>;
  synthesizeSegment?(segment: NarrationSegment, outputPath: string): Promise<TTSResult>;
};