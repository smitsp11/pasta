import { animate } from "motion";
import { useEffect, useState } from "react";
export function NumberTick({ value, duration = 1.2, instant = false, format = (n: number) => String(Math.round(n)) }: { value: number; duration?: number; instant?: boolean; format?: (n: number) => string }) {
  const [n, setN] = useState(instant ? value : 0);
  useEffect(() => {
    if (instant) { setN(value); return; }
    const ctrl = animate(0, value, { duration, ease: "easeOut", onUpdate: setN });
    return () => ctrl.stop();
  }, [value, instant, duration]);
  return <>{format(n)}</>;
}
