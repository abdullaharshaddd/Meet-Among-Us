import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useConsentNotice, useMeeting, useSetConsent } from "@/api/meetings";
import { BilingualText, Button, Card, Checkbox, Header, LargeTitle, Screen, Skeleton, Text, useToast } from "@/components/ui";
import { layout, space } from "@/theme/tokens";

// Everyone in the meeting agrees to be recorded before it can be processed. You answer for yourself. The host
// answers for named guests, who have no account to answer with.
export default function ConsentScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { data: notice } = useConsentNotice();
  const { data: meeting } = useMeeting(id);
  const setConsent = useSetConsent(id);

  const mine = meeting?.attendees.find((attendee) => attendee.is_me);
  const guests = meeting?.is_host ? meeting.attendees.filter((attendee) => attendee.kind === "guest") : [];

  const answer = (attendeeId: string, granted: boolean) =>
    setConsent.mutate({ attendeeId, granted }, { onError: (error) => toast.show(error.message) });

  return (
    <Screen>
      <Header title="Recording consent" onBack={() => router.back()} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: layout.screenGutter, paddingTop: space.lg, paddingBottom: space["5xl"], gap: layout.sectionGap }}>
        <LargeTitle>{notice?.title ?? "Before this meeting is recorded"}</LargeTitle>

        {!notice && <Skeleton height={space["4xl"]} />}
        <View style={{ gap: space.md }}>
          {notice?.paragraphs.map((paragraph) => (
            <BilingualText key={paragraph} tone="secondary">
              {paragraph}
            </BilingualText>
          ))}
        </View>

        {mine && (
          <Card style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Your answer
            </Text>
            <Text variant="callout" tone="secondary">
              {mine.consent ? (mine.consent.granted ? "You agreed." : "You said no. The meeting can't be processed unless you agree or the host removes you.") : "You haven't answered yet."}
            </Text>
            <Button label="I agree to be recorded" loading={setConsent.isPending && setConsent.variables?.attendeeId === mine.id} onPress={() => answer(mine.id, true)} />
            <Button label="I don't agree" variant="secondary" onPress={() => answer(mine.id, false)} />
          </Card>
        )}

        {guests.length > 0 && (
          <Card style={{ gap: space.md }}>
            <Text variant="label" tone="secondary">
              Guests
            </Text>
            <Text variant="callout" tone="secondary">
              A guest has no account, so you answer for them. Only tick a name once that person has told you they agree.
            </Text>
            {guests.map((guest) => {
              const agreed = guest.consent?.granted === true;

              // The Checkbox draws only the box, so the sentence sits beside it and tapping it toggles too.
              return (
                <View key={guest.id} style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
                  <Checkbox label={`${guest.name} agrees to be recorded`} checked={agreed} onChange={(checked) => answer(guest.id, checked)} />
                  <Text variant="body" style={{ flex: 1 }} onPress={() => answer(guest.id, !agreed)}>
                    {`${guest.name} agrees to be recorded`}
                  </Text>
                </View>
              );
            })}
          </Card>
        )}

        {meeting && !meeting.consent_ready && (
          <Text variant="callout" tone="secondary">
            Still waiting for: {meeting.waiting_for_consent.join(", ")}.
          </Text>
        )}

        <Button label="Done" variant={meeting?.consent_ready ? "primary" : "secondary"} onPress={() => router.back()} />
      </ScrollView>
    </Screen>
  );
}
