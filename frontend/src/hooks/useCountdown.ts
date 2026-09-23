import { useEffect, useState } from "react";

interface Countdown {
  msRemaining: number;
  isOver: boolean;
}

export function useCountdown(target: Date | null): Countdown {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!target) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [target]);

  if (!target) {
    return { msRemaining: 0, isOver: false };
  }

  const msRemaining = Math.max(target.getTime() - now, 0);
  return { msRemaining, isOver: msRemaining <= 0 };
}
