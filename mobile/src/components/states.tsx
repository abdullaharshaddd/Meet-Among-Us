import type { ReactNode } from "react";
import { ActivityIndicator, View, StyleSheet } from "react-native";
import { colors, radii, space } from "@/theme/tokens";
import { Text } from "./Text";
import { Button } from "./Button";

// EmptyState, ErrorState, and LoadingState are the same panel — a centered
// glyph, a title, an optional description, an optional action — so they
// share one layout instead of three near-identical ones.
function Panel({
  glyph,
  title,
  description,
  action,
}: {
  glyph: ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onPress: () => void };
}) {
  return (
    <View style={styles.panel}>
      {glyph}
      <Text variant="heading" style={styles.title}>
        {title}
      </Text>
      {description && (
        <Text variant="body" tone="secondary" style={styles.description}>
          {description}
        </Text>
      )}
      {action && <Button label={action.label} variant="secondary" onPress={action.onPress} />}
    </View>
  );
}

function GlyphPlate({ char, tone }: { char: string; tone?: "danger" }) {
  return (
    <View style={[styles.plate, tone === "danger" && { borderColor: colors.state.danger }]}>
      <Text variant="title" tone={tone ?? "tertiary"}>
        {char}
      </Text>
    </View>
  );
}

// A stub screen's glyph and copy say what's coming, not just "TODO" —
// callers pass both, this doesn't default them.
export function EmptyState({
  glyph,
  ...rest
}: {
  glyph: string;
  title: string;
  description?: string;
  action?: { label: string; onPress: () => void };
}) {
  return <Panel glyph={<GlyphPlate char={glyph} />} {...rest} />;
}

// `description` is required and not defaulted — "Something went wrong"
// is banned by the copy rules, so every call site must say what happened.
export function ErrorState(props: { title?: string; description: string; onRetry?: () => void }) {
  return (
    <Panel
      glyph={<GlyphPlate char="!" tone="danger" />}
      title={props.title ?? "Couldn't load this"}
      description={props.description}
      action={props.onRetry ? { label: "Try again", onPress: props.onRetry } : undefined}
    />
  );
}

export function LoadingState({ label }: { label?: string }) {
  return (
    <View style={styles.panel}>
      <ActivityIndicator color={colors.accent.base} size="large" />
      {label && (
        <Text variant="body" tone="secondary" style={styles.description}>
          {label}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    alignItems: "center",
    justifyContent: "center",
    gap: space.md,
    padding: space.xxl,
  },
  plate: {
    width: 56,
    height: 56,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border.default,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    textAlign: "center",
  },
  description: {
    textAlign: "center",
  },
});
