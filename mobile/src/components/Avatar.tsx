import { Image } from "expo-image";
import { View } from "react-native";
import { colors, radii } from "@/theme/tokens";
import { Text } from "./Text";

type Size = "sm" | "md" | "lg";

const DIAMETER: Record<Size, number> = { sm: 28, md: 40, lg: 56 };
const FONT_VARIANT: Record<Size, "caption" | "label" | "heading"> = {
  sm: "caption",
  md: "label",
  lg: "heading",
};

export interface AvatarProps {
  name: string;
  imageUrl?: string | null;
  size?: Size;
}

// avatar_url is nullable in the schema (Google-only sign-ups may lack one,
// and email/password sign-ups always do) — initials are the default state,
// not a fallback for errors.
export function Avatar({ name, imageUrl, size = "md" }: AvatarProps) {
  const diameter = DIAMETER[size];
  const style = {
    width: diameter,
    height: diameter,
    borderRadius: radii.pill,
  };

  if (imageUrl) {
    return <Image source={{ uri: imageUrl }} style={style} />;
  }

  const initials = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();

  return (
    <View style={[style, { backgroundColor: colors.accent.subtle, alignItems: "center", justifyContent: "center" }]}>
      <Text variant={FONT_VARIANT[size]} tone="accent">
        {initials}
      </Text>
    </View>
  );
}
