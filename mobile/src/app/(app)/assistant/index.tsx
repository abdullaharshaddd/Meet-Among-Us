import { useEffect, useRef, useState } from "react";
import { Pressable, ScrollView, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  ActionConfirmCard,
  BilingualText,
  BottomSheet,
  CitationChip,
  FilterChip,
  Header,
  Icon,
  LoadingDots,
  Screen,
  Text,
  useDockClearance,
  useToast,
} from "@/components/ui";
import { Composer } from "@/features/assistant/Composer";
import { findMeeting } from "@/mocks/meetings";
import { mockReply, scopes, suggestions, type MockReply } from "@/mocks/assistant";
import { useTheme } from "@/theme/ThemeProvider";
import { borders, layout, radii, ratios, sizes, space } from "@/theme/tokens";

interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
  reply?: MockReply;
}

const REPLY_DELAY = 1000;

export default function AssistantScreen() {
  const router = useRouter();
  const toast = useToast();
  const { colors } = useTheme();
  const { width } = useWindowDimensions();
  const { scope: scopeParam } = useLocalSearchParams<{ scope?: string }>();
  const dockClearance = useDockClearance(true);
  const scroller = useRef<ScrollView>(null);
  const nextId = useRef(1);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [scopeId, setScopeId] = useState("all");
  const [isPickingScope, setIsPickingScope] = useState(false);

  // Arriving from a meeting limits the question to that meeting.
  useEffect(() => {
    if (scopeParam) setScopeId(scopeParam);
  }, [scopeParam]);

  const scopeLabel = scopes.find((scope) => scope.id === scopeId)?.label ?? findMeeting(scopeId)?.title ?? "All meetings";

  const send = (text: string) => {
    const id = nextId.current;
    nextId.current += 2;

    setMessages((current) => [...current, { id, role: "user", text }]);
    setIsThinking(true);

    setTimeout(() => {
      const reply = mockReply(text);

      setMessages((current) => [...current, { id: id + 1, role: "assistant", text: reply.text, reply }]);
      setIsThinking(false);
    }, REPLY_DELAY);
  };

  useEffect(() => {
    scroller.current?.scrollToEnd({ animated: true });
  }, [messages.length, isThinking]);

  const openCitation = (meetingId: string) => router.push({ pathname: "/(app)/meetings/[id]", params: { id: meetingId } });

  return (
    <Screen>
      <Header title="Assistant" />

      <View style={{ paddingHorizontal: layout.screenGutter, paddingVertical: space.sm, flexDirection: "row", alignItems: "center", gap: space.sm }}>
        <Text variant="label" tone="secondary">
          Scope
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Scope: ${scopeLabel}. Tap to change.`}
          onPress={() => setIsPickingScope(true)}
          style={{
            flexDirection: "row",
            alignItems: "center",
            gap: space.sm,
            minHeight: sizes.hitMin,
            paddingHorizontal: space.md,
            borderRadius: radii.sm,
            borderWidth: borders.thin,
            borderColor: colors.borderControl,
            flexShrink: 1,
          }}
        >
          <Text variant="subhead" numberOfLines={1} style={{ flexShrink: 1 }}>
            {scopeLabel}
          </Text>
          <Icon name="chevronDown" size="sm" color={colors.textSecondary} />
        </Pressable>
      </View>

      <ScrollView
        ref={scroller}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: dockClearance, gap: layout.sectionGap }}
      >
        {messages.length === 0 && (
          <View style={{ gap: space.xl }}>
            <View style={{ gap: space.sm }}>
              <BilingualText variant="displayMd">Ask about your meetings</BilingualText>
              <Text variant="callout" tone="secondary">
                Answers come from what was said, with a link to the exact moment. Anything that changes something asks you first.
              </Text>
            </View>

            <View>
              {suggestions.map((suggestion) => (
                <Pressable
                  key={suggestion}
                  accessibilityRole="button"
                  onPress={() => send(suggestion)}
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: space.md,
                    minHeight: sizes.dockHeight,
                    borderBottomWidth: borders.hairline,
                    borderBottomColor: colors.border,
                  }}
                >
                  <BilingualText style={{ flex: 1 }}>{suggestion}</BilingualText>
                  <Icon name="chevronRight" size="md" color={colors.textSecondary} />
                </Pressable>
              ))}
            </View>
          </View>
        )}

        {messages.map((message) =>
          message.role === "user" ? (
            <View
              key={message.id}
              style={{
                alignSelf: "flex-end",
                maxWidth: width * ratios.bubbleMaxWidth,
                paddingVertical: space.md,
                paddingHorizontal: space.lg,
                borderRadius: radii.lg,
                backgroundColor: colors.ink,
              }}
            >
              <BilingualText tone="onInk">{message.text}</BilingualText>
            </View>
          ) : (
            <View key={message.id} style={{ gap: space.md }}>
              <BilingualText>{message.text}</BilingualText>

              {message.reply?.kind === "answer" && (
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
                  {message.reply.citations.map((citation) => (
                    <CitationChip key={citation.label} label={citation.label} onPress={() => openCitation(citation.meetingId)} />
                  ))}
                </View>
              )}

              {message.reply?.kind === "action" && (
                <ActionConfirmCard
                  action={message.reply.action}
                  title={message.reply.title}
                  fields={message.reply.fields}
                  onConfirm={() => toast.show("Task created")}
                  onEdit={() => toast.show("Editing isn't wired up in this shell")}
                  onCancel={() => {}}
                />
              )}
            </View>
          ),
        )}

        {isThinking && (
          <View accessibilityLabel="Assistant is thinking" style={{ paddingVertical: space.sm }}>
            <LoadingDots color={colors.textSecondary} />
          </View>
        )}
      </ScrollView>

      <Composer onSend={send} placeholder="Ask about your meetings…" />

      <BottomSheet visible={isPickingScope} onClose={() => setIsPickingScope(false)} title="Limit answers to">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
          {scopes.map((scope) => (
            <FilterChip
              key={scope.id}
              label={scope.label}
              selected={scope.id === scopeId}
              onPress={() => {
                setScopeId(scope.id);
                setIsPickingScope(false);
              }}
            />
          ))}
        </View>
      </BottomSheet>
    </Screen>
  );
}
