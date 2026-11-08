import type { ReactNode } from "react";
import { Pressable, View } from "react-native";
import { Card, Icon, Text, type Tone } from "@/components/ui";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, sizes, space } from "@/theme/tokens";

export function SettingsGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={{ gap: space.sm }}>
      <Text variant="label" tone="secondary">
        {title}
      </Text>
      <Card padded={false}>{children}</Card>
    </View>
  );
}

export interface SettingsRowProps {
  label: string;
  // Small grey text on the right, like the current choice.
  value?: string;
  // Anything richer than text on the right, like a Badge.
  trailing?: ReactNode;
  onPress?: () => void;
  tone?: Tone;
  isLast?: boolean;
}

export function SettingsRow({ label, value, trailing, onPress, tone = "primary", isLast = false }: SettingsRowProps) {
  const { colors } = useTheme();

  const content = (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        gap: space.md,
        minHeight: sizes.dockHeight,
        paddingHorizontal: space.lg,
        borderBottomWidth: isLast ? 0 : borders.hairline,
        borderBottomColor: colors.border,
      }}
    >
      <Text variant="body" tone={tone} style={{ flexShrink: 1 }}>
        {label}
      </Text>

      <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
        {value && (
          <Text variant="callout" tone="secondary" numberOfLines={1} style={{ flexShrink: 1 }}>
            {value}
          </Text>
        )}
        {trailing}
        {onPress && <Icon name="chevronRight" size="md" color={colors.textSecondary} />}
      </View>
    </View>
  );

  if (!onPress) return content;

  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress}>
      {content}
    </Pressable>
  );
}
