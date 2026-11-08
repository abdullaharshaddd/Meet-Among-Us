import {
  useFonts,
  InstrumentSerif_400Regular,
  InstrumentSerif_400Regular_Italic,
} from "@expo-google-fonts/instrument-serif";
import {
  InstrumentSans_400Regular,
  InstrumentSans_500Medium,
  InstrumentSans_600SemiBold,
  InstrumentSans_700Bold,
} from "@expo-google-fonts/instrument-sans";
import { GeistMono_400Regular, GeistMono_500Medium } from "@expo-google-fonts/geist-mono";
import { NotoNastaliqUrdu_400Regular, NotoNastaliqUrdu_500Medium } from "@expo-google-fonts/noto-nastaliq-urdu";

// Keys here must match the strings in fonts.* in tokens.ts exactly.
// That is the name react-native's fontFamily style looks up once the font is loaded.
export function useAppFonts() {
  const [loaded] = useFonts({
    InstrumentSerif_400Regular,
    InstrumentSerif_400Regular_Italic,
    InstrumentSans_400Regular,
    InstrumentSans_500Medium,
    InstrumentSans_600SemiBold,
    InstrumentSans_700Bold,
    GeistMono_400Regular,
    GeistMono_500Medium,
    NotoNastaliqUrdu_400Regular,
    NotoNastaliqUrdu_500Medium,
  });

  return loaded;
}
