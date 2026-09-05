import { View, type ViewProps } from "react-native";
import { elevation, radii, space } from "@/theme/tokens";

export interface CardProps extends ViewProps {
  level?: 1 | 2;
}

// The only two surfaces the design allows. Reach for `level={2}` on
// anything that floats above other content (a modal, a menu) — everything
// else is level 1.
export function Card({ level = 1, style, ...props }: CardProps) {
  return (
    <View
      style={[
        level === 2 ? elevation.two : elevation.one,
        { borderRadius: radii.lg, padding: space.lg },
        style,
      ]}
      {...props}
    />
  );
}
