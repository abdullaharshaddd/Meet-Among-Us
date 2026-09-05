import { useEffect, useMemo, useState } from "react";
import { View, StyleSheet } from "react-native";
import Animated, {
  useAnimatedStyle,
  useFrameCallback,
  useReducedMotion,
  useSharedValue,
  type SharedValue,
} from "react-native-reanimated";
import { colors } from "@/theme/tokens";

type MeterState = "idle" | "capturing" | "paused";

export interface AudioLevelMeterProps {
  /** 0..1 RMS amplitude for the most recent sample. Ignored while paused/idle. */
  level: number;
  state?: MeterState;
  height?: number;
}

const BAR_WIDTH = 2;
const BAR_GAP = 2;
const PITCH = BAR_WIDTH + BAR_GAP; // how much horizontal space one bar "costs"
const MIN_BAR_COUNT = 8; // floor for a very narrow container

const MIN_BAR_PX = 3; // silence still reads as a faint continuous line, not gaps
const QUIET_OPACITY = 0.25;
const IDLE_OPACITY = 0.2; // distinct from QUIET_OPACITY — idle is "off," not "listening and hearing nothing"
const PAUSED_OPACITY = 0.5;

// Shared with the enrollment quality gate's clip rejection reason in
// DATA_MODEL.md — this is what lets someone see a bad take coming.
const CLIP_THRESHOLD = 0.98;
const SPEECH_FLOOR = 0.05; // below this, the accessibility label says "silent"

const FRAME_INTERVAL_MS = 1000 / 30; // capped scroll rate — see ADR-0006

/**
 * Signature element: a mirrored, scrolling amplitude tape of hairline bars —
 * a seismograph, not a bar chart or a VU meter. See
 * docs/adr/0006-audio-meter-scrolling-history.md.
 *
 * All bars are accent teal; amplitude is encoded as opacity, not hue, so the
 * tape reads as one continuous signal instead of switching colors. The one
 * exception is a 2px amber tick capping a bar that's clipping.
 *
 * The ring buffer, the 30fps throttle, and every per-frame bar update run in
 * `useFrameCallback`/`useAnimatedStyle` worklets on the UI thread — nothing
 * here re-renders React on the sample rate, which matters across a 2-hour
 * recording.
 */
export function AudioLevelMeter({ level, state = "idle", height = 56 }: AudioLevelMeterProps) {
  const [width, setWidth] = useState(0);
  const barCount = Math.max(MIN_BAR_COUNT, Math.floor(width / PITCH));
  const voiceCategory = useVoiceCategory(level, state);

  return (
    <View
      style={[styles.wrapper, { height }]}
      onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
      accessibilityLabel="Audio level"
      accessibilityValue={{ text: voiceCategory }}
    >
      {width > 0 && (
        // Keyed on barCount so a width change (rotation, resize) remounts
        // the ring buffer at its new size instead of patching it in place.
        <MeterTape key={barCount} level={level} state={state} height={height} barCount={barCount} />
      )}
    </View>
  );
}

function useVoiceCategory(level: number, state: MeterState) {
  const [category, setCategory] = useState<"silent" | "capturing" | "too loud" | "paused">("silent");
  useEffect(() => {
    if (state === "paused") return setCategory("paused");
    if (state !== "capturing") return setCategory("silent");
    setCategory(level >= CLIP_THRESHOLD ? "too loud" : level > SPEECH_FLOOR ? "capturing" : "silent");
  }, [level, state]);
  return category;
}

function representativeWaveform(n: number): number[] {
  // Deterministic, not random — reduced-motion users see the same "shape of
  // audio" every time, not a decorative animation swapped for a decorative still.
  return Array.from({ length: n }, (_, i) => {
    const wave = Math.abs(Math.sin(i * 0.35)) * 0.5 + Math.abs(Math.sin(i * 0.9 + 1)) * 0.3;
    return Math.min(1, 0.15 + wave);
  });
}

function MeterTape({ level, state, height, barCount }: { level: number; state: MeterState; height: number; barCount: number }) {
  const reducedMotion = useReducedMotion();
  const buffer = useSharedValue<number[]>(new Array(barCount).fill(0));
  const cursor = useSharedValue(0);
  const levelShared = useSharedValue(level);
  const stateShared = useSharedValue(state);
  const accumulator = useSharedValue(0);

  useEffect(() => {
    levelShared.value = level;
  }, [level, levelShared]);

  useEffect(() => {
    stateShared.value = state;
  }, [state, stateShared]);

  // Reduced motion swaps the live tape for one fixed, representative shape
  // instead of animating — re-seeded whenever a capturing session starts.
  useEffect(() => {
    if (state === "capturing" && reducedMotion) {
      buffer.value = representativeWaveform(barCount);
    }
  }, [state, reducedMotion, barCount, buffer]);

  const frameCallback = useFrameCallback((frameInfo) => {
    "worklet";
    // Runs at the display's native refresh rate but only does work every
    // ~33ms — a real 60/120Hz callback would cost battery for no visible
    // benefit on a tape that scrolls a fixed number of steps per second.
    accumulator.value += frameInfo.timeSincePreviousFrame ?? FRAME_INTERVAL_MS;
    if (accumulator.value < FRAME_INTERVAL_MS) return;
    accumulator.value -= FRAME_INTERVAL_MS;

    const writeIndex = cursor.value % barCount;
    const next = buffer.value.slice();
    next[writeIndex] = levelShared.value;
    buffer.value = next;
    cursor.value += 1;
  }, false);

  useEffect(() => {
    // Idle and paused don't run the tape at all — paused freezes the last
    // frame in place (dimmed by the wrapper below), idle never started one.
    frameCallback.setActive(state === "capturing" && !reducedMotion);
  }, [state, reducedMotion, frameCallback]);

  return (
    <View style={[styles.row, state === "paused" && styles.paused]}>
      {Array.from({ length: barCount }, (_, i) => (
        <Bar key={i} index={i} buffer={buffer} cursor={cursor} barCount={barCount} height={height} stateShared={stateShared} />
      ))}
    </View>
  );
}

function Bar({
  index,
  buffer,
  cursor,
  barCount,
  height,
  stateShared,
}: {
  index: number;
  buffer: SharedValue<number[]>;
  cursor: SharedValue<number>;
  barCount: number;
  height: number;
  stateShared: SharedValue<MeterState>;
}) {
  const style = useAnimatedStyle(() => {
    if (stateShared.value === "idle") {
      // Forced flat, regardless of whatever's left in the buffer from a
      // previous capture — idle must never show stale audio.
      return { height: MIN_BAR_PX, opacity: IDLE_OPACITY };
    }

    const ringIndex = (cursor.value + index) % barCount;
    const value = buffer.value[ringIndex] ?? 0;

    // No withTiming/withSpring — each step is a hard cut to the new sample,
    // which is what makes this read as a seismograph rather than a bouncing
    // bar chart.
    return {
      height: Math.min(height, Math.max(MIN_BAR_PX, value * height)),
      opacity: Math.min(1, QUIET_OPACITY + value * (1 - QUIET_OPACITY)),
    };
  });

  const clipStyle = useAnimatedStyle(() => {
    const ringIndex = (cursor.value + index) % barCount;
    const value = buffer.value[ringIndex] ?? 0;
    return { opacity: stateShared.value !== "idle" && value >= CLIP_THRESHOLD ? 1 : 0 };
  });

  return (
    <Animated.View style={[styles.bar, style]}>
      <Animated.View style={[styles.clipTick, clipStyle]} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    justifyContent: "center",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: BAR_GAP,
  },
  paused: {
    opacity: PAUSED_OPACITY,
  },
  bar: {
    width: BAR_WIDTH,
    borderRadius: BAR_WIDTH / 2, // fully rounded caps on a 2px-wide line
    backgroundColor: colors.accent.base,
  },
  clipTick: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    borderRadius: 1,
    backgroundColor: colors.state.warning,
  },
});
