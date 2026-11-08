import { Text as RNText } from "react-native";
import { guessDirection, splitRuns, type TextDirection } from "@/lib/scriptRuns";
import { type, type TypeStep } from "@/theme/tokens";
import { Text, type TextProps } from "./Text";

type UrduStep = "urduBody" | "urduTitle" | "urduCaption";

// Which Nastaliq step sits next to each Latin step, so a caller only picks one variant.
const URDU_FOR: Partial<Record<TypeStep, UrduStep>> = {
  displayXl: "urduTitle",
  displayLg: "urduTitle",
  displayMd: "urduTitle",
  displayItalic: "urduTitle",
  title: "urduTitle",
  headline: "urduTitle",
  caption: "urduCaption",
  subhead: "urduCaption",
};

const RIGHT_TO_LEFT_MARK = "\u200F";
const LEFT_TO_RIGHT_MARK = "\u200E";
const LEFT_TO_RIGHT_ISOLATE = "\u2066";
const POP_ISOLATE = "\u2069";

// Names and timestamps inside an Urdu sentence are sealed off, so "15:00" and
// "Thursday" can't be reordered by the neighbouring right-to-left text.
function isolateLatin(piece: string): string {
  const [, before, core, after] = piece.match(/^(\s*)([\s\S]*?)(\s*)$/) ?? [];

  if (!core || !/[\p{L}\p{N}]/u.test(core)) return piece;

  return `${before}${LEFT_TO_RIGHT_ISOLATE}${core}${POP_ISOLATE}${after}`;
}

export interface BilingualTextProps extends Omit<TextProps, "children"> {
  children: string;
  // Sets the Latin run. The Urdu run gets the matching Nastaliq step.
  variant?: TypeStep;
  // The line's base direction. Pass "rtl" or "ltr" when the language is known (a transcript
  // segment's `language`). "auto" guesses from which script has more words, for chat and free text.
  direction?: TextDirection | "auto";
}

export function BilingualText({ children, variant = "body", direction = "auto", style, ...props }: BilingualTextProps) {
  const runs = splitRuns(children);
  const hasUrdu = runs.some((run) => run.isUrdu);

  if (!hasUrdu) {
    return (
      <Text
        variant={variant}
        style={[direction === "rtl" && { writingDirection: "rtl", textAlign: "right" }, style]}
        {...props}
      >
        {children}
      </Text>
    );
  }

  const urduStep = type[URDU_FOR[variant] ?? "urduBody"];
  const lineDirection = direction === "auto" ? guessDirection(children) : direction;
  const isRtl = lineDirection === "rtl";
  // The marks pin the base direction on platforms that otherwise pick it from the first letter.
  const directionMark = isRtl ? RIGHT_TO_LEFT_MARK : runs[0].isUrdu ? LEFT_TO_RIGHT_MARK : "";

  // The outer line height has to be the Nastaliq one, or its tall strokes get clipped on any line that holds Urdu.
  return (
    <Text
      variant={variant}
      accessibilityLabel={children}
      style={[
        { lineHeight: urduStep.lineHeight, writingDirection: lineDirection, textAlign: isRtl ? "right" : "left" },
        style,
      ]}
      {...props}
    >
      {directionMark}
      {runs.map((run, index) =>
        run.isUrdu ? (
          <RNText key={index} style={{ fontFamily: urduStep.fontFamily, fontSize: urduStep.fontSize, letterSpacing: urduStep.letterSpacing, includeFontPadding: false }}>
            {run.text}
          </RNText>
        ) : (
          <RNText key={index}>{isolateLatin(run.text)}</RNText>
        ),
      )}
    </Text>
  );
}
