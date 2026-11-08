import { useState } from "react";
import { View } from "react-native";
import { staticWaveform } from "@/lib/waveform";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, opacity, sizes } from "@/theme/tokens";

export interface MeterStripProps {
  height?: number;
  // Draws the last bar in the signal orange. Only for a strip that sits on a recording screen.
  live?: boolean;
}

// A frozen level meter used as a mark on empty and welcome screens. It never moves.
export function MeterStrip({ height = sizes.avatarMd, live = false }: MeterStripProps) {
  const { colors } = useTheme();
  const [width, setWidth] = useState(0);

  const pitch = sizes.meterBar + sizes.meterGap;
  const count = Math.max(0, Math.floor((width + sizes.meterGap) / pitch));
  const levels = staticWaveform(count);

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
      style={{ height, justifyContent: "center" }}
    >
      <View
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          height: borders.hairline,
          backgroundColor: colors.borderStrong,
        }}
      />

      <View style={{ flexDirection: "row", alignItems: "center", gap: sizes.meterGap }}>
        {levels.map((level, index) => {
          const isLast = index === levels.length - 1;

          return (
            <View
              key={index}
              style={{
                width: sizes.meterBar,
                height: Math.max(sizes.meterBar, level * height),
                borderRadius: sizes.meterBar / 2,
                backgroundColor: live && isLast ? colors.signal : colors.ink,
                opacity: live && isLast ? 1 : opacity.dim + level * opacity.dim,
              }}
            />
          );
        })}
      </View>
    </View>
  );
}
