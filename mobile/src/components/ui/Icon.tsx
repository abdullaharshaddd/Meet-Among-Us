import { SymbolView } from "expo-symbols";
import { useTheme } from "@/theme/ThemeProvider";
import { sizes } from "@/theme/tokens";

// SF Symbols on iOS, Material Symbols on Android and web. One entry per icon
// the app uses, so a screen asks for "copy" and never for a platform name.
const icons = {
  add: { ios: "plus", android: "add" },
  check: { ios: "checkmark", android: "check" },
  close: { ios: "xmark", android: "close" },
  chevronRight: { ios: "chevron.right", android: "chevron_right" },
  copy: { ios: "doc.on.doc", android: "content_copy" },
  edit: { ios: "pencil", android: "edit" },
  warning: { ios: "exclamationmark.triangle", android: "warning" },
  search: { ios: "magnifyingglass", android: "search" },
  back: { ios: "chevron.left", android: "chevron_left" },
  chevronDown: { ios: "chevron.down", android: "expand_more" },
  more: { ios: "ellipsis", android: "more_horiz" },
  pause: { ios: "pause.fill", android: "pause" },
  play: { ios: "play.fill", android: "play_arrow" },
  bookmark: { ios: "bookmark", android: "bookmark" },
  send: { ios: "arrow.up", android: "arrow_upward" },
  arrowDown: { ios: "arrow.down", android: "arrow_downward" },
  arrowUp: { ios: "arrow.up", android: "arrow_upward" },
  replay: { ios: "arrow.counterclockwise", android: "replay" },
  sync: { ios: "arrow.triangle.2.circlepath", android: "sync" },
  minimise: { ios: "chevron.down", android: "keyboard_arrow_down" },
  tabMeetings: { ios: "waveform", android: "graphic_eq" },
  tabTasks: { ios: "checkmark.circle", android: "task_alt" },
  tabAssistant: { ios: "bubble.left", android: "chat_bubble" },
  tabSettings: { ios: "gearshape", android: "settings" },
} as const;

export type IconName = keyof typeof icons;

export interface IconProps {
  name: IconName;
  size?: keyof typeof sizes.icon;
  color?: string;
}

export function Icon({ name, size = "md", color }: IconProps) {
  const { colors } = useTheme();
  const symbol = icons[name];

  return (
    <SymbolView
      name={{ ios: symbol.ios, android: symbol.android, web: symbol.android }}
      size={sizes.icon[size]}
      tintColor={color ?? colors.textPrimary}
    />
  );
}
