import { useEffect, useState } from "react";
const CHARS = "!<>-_\\/[]{}—=+*^?#________";
export function TextScramble({ children, duration = 0.8, speed = 0.04, as: Tag = "span", className, style, trigger = true }:
  { children: string; duration?: number; speed?: number; as?: any; className?: string; style?: React.CSSProperties; trigger?: boolean }) {
  const [text, setText] = useState(trigger ? "" : children);
  useEffect(() => {
    if (!trigger) { setText(children); return; }
    const steps = Math.max(1, Math.floor(duration / speed)); let step = 0;
    const id = setInterval(() => {
      step++; const p = step / steps;
      setText(children.split("").map((ch, i) => ch === " " ? " " : i / children.length < p ? ch : CHARS[Math.floor(Math.random() * CHARS.length)]).join(""));
      if (step >= steps) { clearInterval(id); setText(children); }
    }, speed * 1000);
    return () => clearInterval(id);
  }, [children, trigger, duration, speed]);
  return <Tag className={className} style={style}>{text}</Tag>;
}
