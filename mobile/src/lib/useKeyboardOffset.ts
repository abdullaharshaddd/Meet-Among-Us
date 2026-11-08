import { useEffect, useState } from "react";
import { Keyboard, Platform } from "react-native";

// How far a bottom dock has to lift when the keyboard opens. On Android the window itself
// shrinks to make room, so the dock is already above the keyboard and only needs to know it is open.
export function useKeyboard() {
  const [height, setHeight] = useState(0);

  useEffect(() => {
    const showEvent = Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const hideEvent = Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";

    const showSubscription = Keyboard.addListener(showEvent, (event) => setHeight(event.endCoordinates.height));
    const hideSubscription = Keyboard.addListener(hideEvent, () => setHeight(0));

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  return {
    isOpen: height > 0,
    // Only iOS needs the dock lifted by hand.
    lift: Platform.OS === "ios" ? height : 0,
  };
}
