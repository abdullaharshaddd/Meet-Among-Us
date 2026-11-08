import { Text as RNText, View } from "react-native";
import { MeterStrip, Text } from "@/components/ui";
import { fonts, space } from "@/theme/tokens";

export interface AuthHeroProps {
  // The mono line above the headline.
  eyebrow: string;
  // The headline before the italic word.
  headline: string;
  // The one word set in Instrument Serif italic.
  accent: string;
  subtitle: string;
}

export function AuthHero({ eyebrow, headline, accent, subtitle }: AuthHeroProps) {
  return (
    <View style={{ gap: space.lg }}>
      <Text variant="label" tone="secondary">
        {eyebrow}
      </Text>

      <Text variant="displayXl" accessibilityRole="header">
        {headline} <RNText style={{ fontFamily: fonts.serifItalic }}>{accent}</RNText>
      </Text>

      <MeterStrip />

      <Text variant="callout" tone="secondary">
        {subtitle}
      </Text>
    </View>
  );
}
