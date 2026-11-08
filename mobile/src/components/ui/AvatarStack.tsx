import { View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, radii, sizes, space } from "@/theme/tokens";
import { Avatar } from "./Avatar";
import { Text } from "./Text";

export interface StackPerson {
  id: string;
  name: string;
  isGuest?: boolean;
  imageUrl?: string | null;
}

export interface AvatarStackProps {
  people: StackPerson[];
  max?: number;
}

export function AvatarStack({ people, max = 4 }: AvatarStackProps) {
  const { colors } = useTheme();

  const shown = people.slice(0, max);
  const hiddenCount = people.length - shown.length;
  const guestCount = people.filter((person) => person.isGuest).length;

  const summary = `${people.length} ${people.length === 1 ? "person" : "people"}${guestCount > 0 ? `, ${guestCount} guest` : ""}`;

  return (
    <View accessible accessibilityLabel={summary} style={{ flexDirection: "row", alignItems: "center" }}>
      {shown.map((person, index) => (
        <View key={person.id} style={{ marginLeft: index === 0 ? 0 : -space.sm }}>
          <Avatar personId={person.id} name={person.name} size="sm" isGuest={person.isGuest} imageUrl={person.imageUrl} />
        </View>
      ))}

      {hiddenCount > 0 && (
        <View
          style={{
            marginLeft: -space.sm,
            minWidth: sizes.avatarSm,
            height: sizes.avatarSm,
            paddingHorizontal: space.xs,
            borderRadius: radii.pill,
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: colors.sunken,
            borderWidth: borders.hairline,
            borderColor: colors.border,
          }}
        >
          <Text variant="label">+{hiddenCount}</Text>
        </View>
      )}
    </View>
  );
}
