// Temporary dev screen for checking tokens and components on a real display. Deleted before release.
import type { ReactNode } from "react";
import { Platform, Pressable, ScrollView, StyleSheet, Text, View, type TextStyle, type ViewStyle } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { ComponentPreviews } from "@/components/ui/preview";
import { useTheme } from "@/theme/ThemeProvider";
import { useThemeStore } from "@/theme/themeStore";
import { contrastRatio } from "@/theme/contrast";
import { speakerHues } from "@/theme/speakerHues";
import { borders, layout, palettes, radii, sizes, space, type, type Scheme, type TypeStep } from "@/theme/tokens";

const URDU_SAMPLE = "آج کی میٹنگ میں تین فیصلے ہوئے";
const CODE_SWITCHED_SAMPLE = "Kal ki meeting mein launch date final hui — ہم نے Thursday 15:00 رکھا";

// A run of Arabic-script words, with the spaces and Urdu commas between them.
const URDU_RUN = /([؀-ۿ]+(?:[\s،۔]+[؀-ۿ]+)*)/;

const PHONE_WIDTH = 430;

type ThemeChoice = Scheme | "system";

const CHOICE_LABELS: Record<ThemeChoice, string> = { system: "System", light: "Paper", dark: "Studio" };

const COLOR_GROUPS: { title: string; keys: (keyof typeof palettes.light)[] }[] = [
  { title: "Surfaces", keys: ["canvas", "surface", "raised", "sunken"] },
  { title: "Lines", keys: ["border", "borderStrong", "borderControl"] },
  { title: "Text", keys: ["textPrimary", "textSecondary", "textTertiary"] },
  { title: "Ink", keys: ["ink", "onInk"] },
  { title: "Signal (recording only)", keys: ["signal", "onSignal", "signalText", "signalWash"] },
  { title: "Status", keys: ["success", "warning", "danger"] },
  { title: "Other", keys: ["focusRing", "scrim"] },
];

function sampleFor(step: TypeStep): string {
  if (step.startsWith("urdu")) return URDU_SAMPLE;
  if (step === "displayItalic") return "remembered";
  if (step === "timer") return "00:42:17";
  if (step === "mono") return "CHUNK 47 · 00:42:17";
  if (step === "label") return "Scheduled · Tue 4 Nov";
  if (step.startsWith("display")) return "Weekly sync";

  return "Quarterly planning review";
}

export default function DesignSystemScreen() {
  const router = useRouter();
  const { colors, shadow, scheme } = useTheme();
  const override = useThemeStore((state) => state.override);
  const setOverride = useThemeStore((state) => state.setOverride);

  // The route file ships in every build, so release builds bounce out here.
  if (!__DEV__) {
    return <Redirect href="/" />;
  }

  const choice: ThemeChoice = override ?? "system";

  // On web the page is a phone-width column with canvas around it. Native stays full width.
  const webPhoneColumn: ViewStyle | false =
    Platform.OS === "web" && {
      width: "100%",
      maxWidth: PHONE_WIDTH,
      alignSelf: "center",
      borderLeftWidth: StyleSheet.hairlineWidth,
      borderRightWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    };

  const words = (step: TypeStep, color: string = colors.textPrimary): TextStyle => ({ ...type[step], color });

  const Section = ({ title, children }: { title: string; children: ReactNode }) => (
    <View style={{ gap: space.md }}>
      <Text style={words("label", colors.textSecondary)}>{title}</Text>
      {children}
    </View>
  );

  const codeSwitchedRuns = CODE_SWITCHED_SAMPLE.split(URDU_RUN).filter((run) => run.length > 0);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.canvas }}>
      <ScrollView contentContainerStyle={[{ padding: layout.screenGutter, gap: layout.sectionGap }, webPhoneColumn]}>
        <View style={{ gap: space.sm }}>
          <Text style={words("displayLg")}>Design system</Text>
          <Text style={words("callout", colors.textSecondary)}>
            Showing {scheme === "light" ? "Paper" : "Studio"}. Dev only, removed before release.
          </Text>
          <Pressable
            onPress={() => router.back()}
            hitSlop={space.md}
            style={{ minHeight: sizes.hitMin, justifyContent: "center", alignSelf: "flex-start" }}
          >
            <Text style={words("button")}>Close</Text>
          </Pressable>
        </View>

        <Section title="Theme">
          <View style={{ flexDirection: "row", gap: space.sm }}>
            {(Object.keys(CHOICE_LABELS) as ThemeChoice[]).map((option) => {
              const isSelected = option === choice;

              return (
                <Pressable
                  key={option}
                  onPress={() => setOverride(option === "system" ? null : option)}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                  style={{
                    flex: 1,
                    minHeight: sizes.segmentedHeight,
                    alignItems: "center",
                    justifyContent: "center",
                    borderRadius: radii.md,
                    borderWidth: borders.thin,
                    borderColor: isSelected ? colors.ink : colors.borderStrong,
                    backgroundColor: isSelected ? colors.ink : "transparent",
                  }}
                >
                  <Text style={words("subhead", isSelected ? colors.onInk : colors.textPrimary)}>{CHOICE_LABELS[option]}</Text>
                </Pressable>
              );
            })}
          </View>
        </Section>

        <ComponentPreviews />

        <Section title="Colors · contrast is against canvas">
          <View style={{ gap: space.xl }}>
            {COLOR_GROUPS.map((group) => (
              <View key={group.title} style={{ gap: space.sm }}>
                <Text style={words("caption", colors.textSecondary)}>{group.title}</Text>
                {group.keys.map((key) => {
                  const value = colors[key];
                  const ratio = contrastRatio(value, colors.canvas);

                  return (
                    <View key={key} style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
                      <View
                        style={{
                          width: sizes.avatarMd,
                          height: sizes.avatarMd,
                          borderRadius: radii.sm,
                          backgroundColor: value,
                          borderWidth: borders.hairline,
                          borderColor: colors.borderStrong,
                        }}
                      />
                      <View style={{ flex: 1 }}>
                        <Text style={words("subhead")}>{key}</Text>
                        <Text style={words("mono", colors.textSecondary)}>{value}</Text>
                        {key === "borderControl" && (
                          <Text style={words("mono", colors.textSecondary)}>
                            vs surface {contrastRatio(value, colors.surface)?.toFixed(2)}:1 · must be 3:1 or more
                          </Text>
                        )}
                      </View>
                      <Text style={words("mono", colors.textSecondary)}>{ratio ? `${ratio.toFixed(2)}:1` : "alpha"}</Text>
                    </View>
                  );
                })}
              </View>
            ))}
          </View>
        </Section>

        <Section title="Type">
          <View style={{ gap: space["2xl"] }}>
            {(Object.keys(type) as TypeStep[]).map((step) => {
              const style = type[step];
              const isUrdu = step.startsWith("urdu");

              return (
                <View key={step} style={{ gap: space.xs }}>
                  <Text style={words("mono", colors.textSecondary)}>
                    {step} · {style.fontSize}/{style.lineHeight}
                  </Text>
                  <Text style={[words(step), isUrdu && { writingDirection: "rtl", textAlign: "right" }]}>{sampleFor(step)}</Text>
                </View>
              );
            })}

            <View style={{ gap: space.xs }}>
              <Text style={words("mono", colors.textSecondary)}>code-switched line (temporary split until BilingualText)</Text>
              <Text style={words("urduBody")}>
                {codeSwitchedRuns.map((run, index) => (
                  <Text key={index} style={URDU_RUN.test(run) ? words("urduBody") : { ...words("body"), lineHeight: type.urduBody.lineHeight }}>
                    {run}
                  </Text>
                ))}
              </Text>
            </View>
          </View>
        </Section>

        <Section title="Spacing">
          <View style={{ gap: space.xs }}>
            {Object.entries(space).map(([name, value]) => (
              <View key={name} style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
                <Text style={[words("mono", colors.textSecondary), { width: sizes.avatarMd + space.md }]}>
                  {name} {value}
                </Text>
                <View style={{ width: value, height: space.md, backgroundColor: colors.ink }} />
              </View>
            ))}
            <Text style={words("mono", colors.textSecondary)}>
              screenGutter {layout.screenGutter} · cardGap {layout.cardGap} · sectionGap {layout.sectionGap}
            </Text>
          </View>
        </Section>

        <Section title="Radii">
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.lg }}>
            {Object.entries(radii).map(([name, value]) => (
              <View key={name} style={{ alignItems: "center", gap: space.xs }}>
                <View
                  style={{
                    width: sizes.avatarMd + space.lg,
                    height: sizes.avatarMd + space.lg,
                    borderRadius: value,
                    backgroundColor: colors.sunken,
                    borderWidth: borders.thin,
                    borderColor: colors.borderStrong,
                  }}
                />
                <Text style={words("mono", colors.textSecondary)}>
                  {name} {value === radii.pill ? "" : value}
                </Text>
              </View>
            ))}
          </View>
        </Section>

        <Section title="Elevation">
          <View style={{ gap: space.lg }}>
            <View style={{ backgroundColor: colors.surface, borderWidth: borders.hairline, borderColor: colors.border, borderRadius: radii.md, padding: space.lg }}>
              <Text style={words("headline")}>Flat card</Text>
              <Text style={words("callout", colors.textSecondary)}>Surface fill and a hairline. Nothing else.</Text>
            </View>
            <View style={[{ backgroundColor: colors.raised, borderWidth: borders.hairline, borderColor: colors.border, borderRadius: radii.md, padding: space.lg }, shadow]}>
              <Text style={words("headline")}>Floating</Text>
              <Text style={words("callout", colors.textSecondary)}>Docks, sheets and toasts only.</Text>
            </View>
          </View>
        </Section>

        <Section title="Speaker hues · dots, bars and rings, never text">
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.lg }}>
            {speakerHues.map((hue) => {
              const ratio = contrastRatio(hue, colors.canvas);

              return (
                <View key={hue} style={{ alignItems: "center", gap: space.xs }}>
                  <View style={{ flexDirection: "row", gap: space.sm }}>
                    <View style={{ width: space.xl, height: space.xl, borderRadius: radii.pill, backgroundColor: hue }} />
                    <View style={{ width: space.xl, height: space.xl, borderRadius: radii.pill, borderWidth: borders.focus, borderColor: hue }} />
                  </View>
                  <Text style={words("mono", colors.textSecondary)}>{hue}</Text>
                  <Text style={words("mono", colors.textSecondary)}>{ratio ? `${ratio.toFixed(2)}:1` : ""}</Text>
                </View>
              );
            })}
          </View>
          <Text style={words("caption", colors.textSecondary)}>Filled is a member. Ringed is a Guest.</Text>
        </Section>

        <Section title="Sizes">
          <View style={{ gap: space.xs }}>
            {Object.entries(sizes)
              .filter(([name]) => name !== "icon")
              .map(([name, value]) => (
                <Text key={name} style={words("mono", colors.textSecondary)}>
                  {name} {String(value)}
                </Text>
              ))}
          </View>
        </Section>
      </ScrollView>
    </SafeAreaView>
  );
}
