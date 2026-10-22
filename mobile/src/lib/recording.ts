import { RecordingPresets, type RecordingOptions } from "expo-audio";

// 16 kHz mono matches what the embedding model wants, so the file is small and
// nothing is thrown away by the server. The 'web' mimeType makes browsers record webm.
export const enrollmentRecordingOptions: RecordingOptions = {
  ...RecordingPresets.HIGH_QUALITY,
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 64000,
  isMeteringEnabled: true,
  web: { mimeType: "audio/webm" },
};

// expo-audio reports metering in dBFS (-160 is silence, 0 is full scale).
// Anything quieter than -60 dB is treated as silence so the meter is readable.
export function meteringToLevel(decibels: number | undefined): number {
  if (decibels === undefined) return 0;

  const level = (decibels + 60) / 60;

  return Math.min(1, Math.max(0, level));
}

export function formatSeconds(milliseconds: number): string {
  return `${(milliseconds / 1000).toFixed(1)}s`;
}
