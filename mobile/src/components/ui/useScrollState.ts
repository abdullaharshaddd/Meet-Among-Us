import { useAnimatedScrollHandler, useSharedValue } from "react-native-reanimated";

// How far a list has scrolled, and whether the person is moving down the list.
// Headers use the distance to fade in a small title; docks use the direction to shrink.
export function useScrollState() {
  const scrollY = useSharedValue(0);
  const isScrollingDown = useSharedValue(false);

  const onScroll = useAnimatedScrollHandler((event) => {
    const y = event.contentOffset.y;
    const change = y - scrollY.value;

    // Small wobbles don't count, and the top of the list always counts as "up".
    if (y <= 0) isScrollingDown.value = false;
    else if (change > 6) isScrollingDown.value = true;
    else if (change < -6) isScrollingDown.value = false;

    scrollY.value = y;
  });

  return { scrollY, isScrollingDown, onScroll };
}
