// Temporary dev preview of the component library, rendered inside app/design-system.tsx.
// Each component adds its own section here as it is built. Deleted before release.
import { useState, type ReactNode } from "react";
import { Text as RNText, View } from "react-native";
import { useTheme } from "@/theme/ThemeProvider";
import { layout, space, type } from "@/theme/tokens";
import { MorePreviews } from "./preview2";
import { Section } from "./PreviewSection";
import { Avatar, AvatarStack, Badge, BilingualText, Button, Card, Input, SpeakerChip, Text, UnknownSpeakerChip, type StackPerson } from "./index";

function ButtonPreview() {
  const [isSaving, setIsSaving] = useState(false);

  const fakeSave = () => {
    setIsSaving(true);
    setTimeout(() => setIsSaving(false), 1800);
  };

  return (
    <Section title="Button" note="Press them: scale to 0.97 and a slight fade. Tab to one on web to see the focus ring.">
      <View style={{ gap: space.sm }}>
        <Button label="Create workspace" onPress={() => {}} />
        <Button label="Join with code" variant="secondary" onPress={() => {}} />
        <Button label="Skip for now" variant="ghost" onPress={() => {}} />
        <Button label="Delete voiceprint" variant="dangerText" onPress={() => {}} />
        <Button label="Start meeting" variant="signal" onPress={() => {}} />
      </View>

      <Text variant="caption" tone="secondary">
        Sizes: dock (56), md (48), sm (40 with a 44 hit area), and an icon
      </Text>
      <View style={{ gap: space.sm }}>
        <Button label="Next passage" size="dock" onPress={() => {}} />
        <Button label="Copy code" size="md" variant="secondary" icon="copy" onPress={() => {}} />
        <View style={{ flexDirection: "row", gap: space.sm }}>
          <Button label="Edit" size="sm" variant="secondary" onPress={() => {}} />
          <Button label="Add" size="sm" icon="add" onPress={() => {}} />
        </View>
      </View>

      <Text variant="caption" tone="secondary">
        Loading and disabled
      </Text>
      <View style={{ gap: space.sm }}>
        <Button label={isSaving ? "Saving" : "Tap to see loading"} loading={isSaving} onPress={fakeSave} />
        <Button label="Create account" loading onPress={() => {}} />
        <Button label="Create account" disabled onPress={() => {}} />
        <Button label="Cancel" variant="secondary" disabled onPress={() => {}} />
        <Button label="Start meeting" variant="signal" loading onPress={() => {}} />
      </View>
    </Section>
  );
}

function CardPreview() {
  const [taps, setTaps] = useState(0);

  return (
    <Section title="Card" note="Flat with a hairline. Only the raised variant casts a shadow.">
      <View style={{ gap: layout.cardGap }}>
        <Card>
          <Text variant="headline">Sprint sync</Text>
          <Text variant="callout" tone="secondary">
            Tue 4 Nov · 14:00 · 48 min
          </Text>
        </Card>

        <Card variant="live">
          <Text variant="label" tone="signal">
            Live · 00:23:41
          </Text>
          <Text variant="headline">Design review</Text>
          <Text variant="callout" tone="secondary">
            Orange wash, no border. For a meeting that is recording now.
          </Text>
        </Card>

        <Card variant="raised">
          <Text variant="headline">Raised</Text>
          <Text variant="callout" tone="secondary">
            Raised fill and a floating shadow.
          </Text>
        </Card>

        <Card onPress={() => setTaps(taps + 1)} accessibilityLabel="Pressable card">
          <Text variant="headline">Pressable card</Text>
          <Text variant="callout" tone="secondary">
            Tapped {taps} times
          </Text>
        </Card>
      </View>
    </Section>
  );
}

function InputPreview() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("Ayesha Siddiqui");
  const [password, setPassword] = useState("");
  const [urdu, setUrdu] = useState("آج کی میٹنگ میں تین فیصلے ہوئے");
  const [notes, setNotes] = useState("");

  const emailError = email.length > 0 && !email.includes("@") ? "Enter an email like name@company.com" : undefined;

  return (
    <Section title="Input" note="Click into a field for the 2 pt ring. The email field shows its error as you type.">
      <View style={{ gap: layout.cardGap }}>
        <Input
          label="Email"
          value={email}
          onChangeText={setEmail}
          error={emailError}
          placeholder="name@company.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <Input label="Name" value={name} onChangeText={setName} helper="Shown to your teammates." />
        <Input label="Password" value={password} onChangeText={setPassword} secure helper="At least 8 characters" />
        <Input label="Urdu text" value={urdu} onChangeText={setUrdu} helper="Starts with an Urdu letter, so it aligns right in Nastaliq." />
        <Input label="Notes" value={notes} onChangeText={setNotes} multiline placeholder="Anything the host should know" />
        <Input label="Workspace" value="Acme Studio" editable={false} />
        <Input label="Join code" value="K7QM-2XPD" error="That code has expired. Ask the owner for a new one." />
      </View>
    </Section>
  );
}

const URDU_ONLY = "آج کی میٹنگ میں تین فیصلے ہوئے";
const URDU_FIRST = "ہم نے launch date Thursday 15:00 رکھی ہے۔";
const LATIN_FIRST = "Kal ki meeting mein launch date final hui — ہم نے Thursday 15:00 رکھا";

function BilingualTextPreview() {
  return (
    <Section title="BilingualText" note="Each run gets its own font. The line height follows Nastaliq whenever a line has any Urdu.">
      <Card style={{ gap: space.lg }}>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            Latin only
          </Text>
          <BilingualText>Let's lock the launch date on Thursday at 15:00.</BilingualText>
        </View>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            Urdu only
          </Text>
          <BilingualText>{URDU_ONLY}</BilingualText>
        </View>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            Latin first, then Urdu
          </Text>
          <BilingualText>{LATIN_FIRST}</BilingualText>
        </View>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            Urdu first, with a name and a timestamp inside
          </Text>
          <BilingualText>{URDU_FIRST}</BilingualText>
        </View>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            As a heading (headline and Nastaliq title)
          </Text>
          <BilingualText variant="headline">Sprint sync — آج کے فیصلے</BilingualText>
        </View>
        <View style={{ gap: space.xxs }}>
          <Text variant="caption" tone="secondary">
            As a caption
          </Text>
          <BilingualText variant="caption" tone="secondary">
            Marked at 23:41 — نشان زد
          </BilingualText>
        </View>
      </Card>
    </Section>
  );
}

function BadgePreview() {
  return (
    <Section title="Badge" note="Meeting states. Orange is only for LIVE.">
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
        <Badge label="Scheduled" />
        <Badge label="Live" variant="live" />
        <Badge label="Processing" variant="warning" />
        <Badge label="Ready" variant="success" />
        <Badge label="Failed" variant="danger" />
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
        <Badge label="Admin" />
        <Badge label="Member" />
        <Badge label="Enrolled" variant="success" />
        <Badge label="Not enrolled" variant="warning" />
      </View>
    </Section>
  );
}

const PEOPLE: StackPerson[] = [
  { id: "user-ayesha", name: "Ayesha Siddiqui" },
  { id: "user-bilal", name: "Bilal Hussain" },
  { id: "user-sara", name: "Sara Khan" },
  { id: "guest-omar", name: "Omar Farooq", isGuest: true },
  { id: "user-hamza", name: "Hamza Raza" },
  { id: "user-noor", name: "Noor Fatima" },
];

function SpeakerPreview() {
  const [renamedTimes, setRenamedTimes] = useState(0);

  return (
    <Section
      title="Speakers"
      note="A Guest is a named outsider and gets a hollow ring and a GUEST tag. An Unknown Speaker is an unmatched voice and gets a dashed outline. They never look alike."
    >
      <Card style={{ gap: space.md }}>
        <Text variant="caption" tone="secondary">
          Named speakers
        </Text>
        <SpeakerChip speakerId="user-ayesha" name="Ayesha Siddiqui" />
        <SpeakerChip speakerId="user-bilal" name="Bilal Hussain" />
        <SpeakerChip speakerId="user-sara" name="Sara Khan" onPress={() => {}} />
        <SpeakerChip speakerId="guest-omar" name="Omar Farooq" isGuest />

        <Text variant="caption" tone="secondary">
          Unmatched voices. Tapping opens the rename sheet (renamed {renamedTimes} times here).
        </Text>
        <Text variant="caption" tone="secondary">
          Dashed outline (the default), then the solid fallback
        </Text>
        <UnknownSpeakerChip number={1} outline="dashed" onPress={() => setRenamedTimes(renamedTimes + 1)} />
        <UnknownSpeakerChip number={2} outline="solid" onPress={() => setRenamedTimes(renamedTimes + 1)} />
      </Card>

      <Card style={{ gap: space.md }}>
        <Text variant="caption" tone="secondary">
          Avatar stack: 3 people, then 6 people (max 4 shown), with a Guest ringed
        </Text>
        <AvatarStack people={PEOPLE.slice(0, 3)} />
        <AvatarStack people={PEOPLE} />
        <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
          <Avatar personId="user-ayesha" name="Ayesha Siddiqui" size="md" />
          <Avatar personId="guest-omar" name="Omar Farooq" size="md" isGuest />
          <Text variant="caption" tone="secondary">
            40 pt: member, then Guest
          </Text>
        </View>
      </Card>
    </Section>
  );
}

const BIDI_LINES = [
  { name: "Latin first, Urdu, then punctuation", text: "We decided ہم نے یہ طے کیا, then moved on." },
  { name: "Urdu first, with a timestamp", text: "میٹنگ 15:00 بجے شروع ہوئی" },
  { name: "Tie (2 words each), goes to RTL", text: "Ali نے 3 tasks لیے" },
  { name: "Urdu majority, Latin first", text: "Sprint ka review ہم نے کل کیا" },
  { name: "Urdu majority, Latin first", text: "Ok تو phir ہم Thursday کو ملتے ہیں" },
  { name: "Control: pure English", text: "Let's lock the launch date on Thursday." },
  { name: "Control: pure Urdu", text: "آج کی میٹنگ میں تین فیصلے ہوئے" },
];

const INVISIBLE_CHARACTERS = [
  { name: "RLM", character: "\u200F" },
  { name: "LRI", character: "\u2066" },
  { name: "RLI", character: "\u2067" },
  { name: "FSI", character: "\u2068" },
  { name: "PDI", character: "\u2069" },
];

function BidiTestPreview() {
  const { colors } = useTheme();

  return (
    <Section
      title="Bidi test"
      note="Auto picks the script with more words, and a tie goes to RTL. Transcript rows will pass the direction instead."
    >
      {BIDI_LINES.map((line) => (
        <Card key={line.text} style={{ gap: space.xs }}>
          <Text variant="caption" tone="secondary">
            {line.name}
          </Text>
          <Text variant="label" tone="secondary">
            direction auto
          </Text>
          <BilingualText>{line.text}</BilingualText>
        </Card>
      ))}

      <Card style={{ gap: space.xs }}>
        <Text variant="caption" tone="secondary">
          The tie line again with the direction given, as a transcript row will pass it from the segment language
        </Text>
        <Text variant="label" tone="secondary">
          direction rtl
        </Text>
        <BilingualText direction="rtl">Ali نے 3 tasks لیے</BilingualText>
        <Text variant="label" tone="secondary">
          direction ltr
        </Text>
        <BilingualText direction="ltr">Ali نے 3 tasks لیے</BilingualText>
      </Card>

      <Card style={{ gap: space.sm }}>
        <Text variant="caption" tone="secondary">
          Invisible characters. Each pair of brackets should look empty. A visible box inside means that character shows as a box on this device. Ignore the bracket order.
        </Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.lg }}>
          {INVISIBLE_CHARACTERS.map((item) => (
            <View key={item.name} style={{ gap: space.xxs }}>
              <Text variant="label" tone="secondary">
                {item.name}
              </Text>
              <Text>{`[${item.character}]`}</Text>
              <RNText style={[type.urduBody, { color: colors.textPrimary, textAlign: "left", writingDirection: "ltr" }]}>{`[${item.character}]`}</RNText>
            </View>
          ))}
        </View>
        <Text variant="caption" tone="secondary">
          Top row is Instrument Sans, bottom row is Nastaliq.
        </Text>
      </Card>
    </Section>
  );
}

export function ComponentPreviews() {
  return (
    <>
      <ButtonPreview />
      <CardPreview />
      <InputPreview />
      <BilingualTextPreview />
      <BidiTestPreview />
      <BadgePreview />
      <SpeakerPreview />
      <MorePreviews />
    </>
  );
}
