import { useEffect, useState } from "react";
import { View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useFrameCallback,
  useReducedMotion,
  useSharedValue,
  type SharedValue,
} from "react-native-reanimated";
import { staticWaveform } from "@/lib/waveform";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, ratios, sizes } from "@/theme/tokens";

type MeterState = "idle" | "capturing" | "paused";

export interface AudioLevelMeterProps {
  // 0..1 amplitude for the most recent sample. Ignored while paused or idle.
  level: number;
  state?: MeterState;
  height?: number;
}

const PITCH = sizes.meterBar + sizes.meterGap;
const MIN_BAR_COUNT = 8;

const QUIET_OPACITY = 0.25;
const IDLE_OPACITY = 0.2;
const PAUSED_OPACITY = 0.5;

const SPEECH_FLOOR = 0.05;

// Capped scroll rate. See ADR-0006.
const FRAME_INTERVAL_MS = 1000 / 30;

// A seismograph tape: the newest sample enters on the right in the signal color and the
// history scrolls left. A peak above -3 dBFS turns the newest bar red for one step.
// The ring buffer and every per-frame update run on the UI thread, so nothing re-renders
// React at the sample rate during a two-hour recording. See ADR-0006.
export function AudioLevelMeter({ level, state = "idle", height = sizes.meterHeightEnroll }: AudioLevelMeterProps) {
  const { colors } = useTheme();
  const [width, setWidth] = useState(0);
  const barCount = Math.max(MIN_BAR_COUNT, Math.floor((width + sizes.meterGap) / PITCH));
  const voiceCategory = useVoiceCategory(level, state);

  return (
    <View
      onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
      accessibilityLabel="Audio level"
      accessibilityValue={{ text: voiceCategory }}
      style={{ height, justifyContent: "center" }}
    >
      <View
        pointerEvents="none"
        style={{ position: "absolute", left: 0, right: 0, height: borders.hairline, backgroundColor: colors.borderStrong }}
      />

      {width > 0 && (
        // Keyed on the bar count so a width change remounts the buffer at its new size.
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

    setCategory(level >= ratios.peakLevel ? "too loud" : level > SPEECH_FLOOR ? "capturing" : "silent");
  }, [level, state]);

  return category;
}

interface TapeProps {
  level: number;
  state: MeterState;
  height: number;
  barCount: number;
}

function MeterTape({ level, state, height, barCount }: TapeProps) {
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

  // Under reduced motion the tape holds one fixed shape instead of scrolling.
  useEffect(() => {
    if (state === "capturing" && reducedMotion) buffer.value = staticWaveform(barCount);
  }, [state, reducedMotion, barCount, buffer]);

  const frameCallback = useFrameCallback((frameInfo) => {
    "worklet";
    // Runs at the display's refresh rate but only does work every ~33 ms.
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
    // Paused freezes the last frame in place, and idle never starts the tape.
    frameCallback.setActive(state === "capturing" && !reducedMotion);
  }, [state, reducedMotion, frameCallback]);

  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end",
        gap: sizes.meterGap,
        opacity: state === "paused" ? PAUSED_OPACITY : 1,
      }}
    >
      {Array.from({ length: barCount }, (_, index) => (
        <Bar
          key={index}
          index={index}
          buffer={buffer}
          cursor={cursor}
          barCount={barCount}
          height={height}
          stateShared={stateShared}
        />
      ))}
    </View>
  );
}

interface BarProps {
  index: number;
  buffer: SharedValue<number[]>;
  cursor: SharedValue<number>;
  barCount: number;
  height: number;
  stateShared: SharedValue<MeterState>;
}

function Bar({ index, buffer, cursor, barCount, height, stateShared }: BarProps) {
  const { colors } = useTheme();
  const isNewest = index === barCount - 1;

  const style = useAnimatedStyle(() => {
    if (stateShared.value === "idle") {
      return { height: sizes.meterBar, opacity: IDLE_OPACITY, backgroundColor: colors.ink };
    }

    const value = buffer.value[(cursor.value + index) % barCount] ?? 0;

    // No easing between samples: each step is a hard cut, which is what makes it read as a seismograph.
    return {
      height: Math.min(height, Math.max(sizes.meterBar, value * height)),
      opacity: isNewest ? 1 : Math.min(1, QUIET_OPACITY + value * (1 - QUIET_OPACITY)),
      backgroundColor: isNewest ? (value >= ratios.peakLevel ? colors.danger : colors.signal) : colors.ink,
    };
  });

  return <Animated.View style={[{ width: sizes.meterBar, borderRadius: sizes.meterBar / 2 }, style]} />;
}
