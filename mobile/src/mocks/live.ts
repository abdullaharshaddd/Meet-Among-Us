// Design shell data – replace with API data
import { useEffect, useState } from "react";

// A fake microphone level for the live-recording shell: a slow swell with some jitter,
// and now and then a loud burst.
export function useMockLevel(isRunning: boolean): number {
  const [level, setLevel] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setLevel(0);
      return;
    }

    let tick = 0;

    const timer = setInterval(() => {
      tick += 1;

      const swell = (Math.sin(tick / 9) + 1) / 2;
      const jitter = Math.random() * 0.25;
      const burst = tick % 97 === 0 ? 0.5 : 0;

      setLevel(Math.min(1, 0.12 + swell * 0.5 + jitter + burst));
    }, 50);

    return () => clearInterval(timer);
  }, [isRunning]);

  return level;
}

export const liveParticipants = [
  { id: "user-ayesha", name: "Ayesha Siddiqui" },
  { id: "user-bilal", name: "Bilal Hussain" },
  { id: "user-sara", name: "Sara Khan" },
  { id: "guest-omar", name: "Omar Farooq", isGuest: true },
];
