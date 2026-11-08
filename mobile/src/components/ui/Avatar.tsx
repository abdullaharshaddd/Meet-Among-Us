import { Image } from "expo-image";
import { View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { speakerHue } from "@/theme/speakerHues";
import { borders, radii, sizes } from "@/theme/tokens";
import { Text } from "./Text";

type Size = "sm" | "md";

const DIAMETERS: Record<Size, number> = { sm: sizes.avatarSm, md: sizes.avatarMd };

export interface AvatarProps {
  // Also picks the ring color for a Guest, so the same person looks the same everywhere.
  personId: string;
  name: string;
  size?: Size;
  // A Guest has no account, so they get a colored ring instead of a photo.
  isGuest?: boolean;
  imageUrl?: string | null;
}

function initialsFor(name: string, count: number): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, count)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

export function Avatar({ personId, name, size = "md", isGuest = false, imageUrl }: AvatarProps) {
  const { colors } = useTheme();
  const diameter = DIAMETERS[size];

  const shape = {
    width: diameter,
    height: diameter,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    backgroundColor: colors.raised,
    borderWidth: isGuest ? borders.focus : borders.hairline,
    borderColor: isGuest ? speakerHue(personId) : colors.border,
  } as const;

  return (
    <View accessible accessibilityLabel={isGuest ? `${name}, guest` : name} style={shape}>
      {imageUrl && !isGuest ? (
        <Image source={{ uri: imageUrl }} style={{ width: diameter, height: diameter }} />
      ) : (
        <Text variant={size === "sm" ? "label" : "subhead"}>{initialsFor(name, size === "sm" ? 1 : 2)}</Text>
      )}
    </View>
  );
}
