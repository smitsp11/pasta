import { motion } from "motion/react";
/** Four corner brackets. Give every Reticle in a group the same layoutId and render it only on the focused target: motion animates it between positions. */
export const Reticle = ({ size = 14, thickness = 2, inset = -6, layoutId = "reticle", color = "var(--scan)" }: { size?: number; thickness?: number; inset?: number; layoutId?: string; color?: string }) => {
  const c = (pos: React.CSSProperties) => <span style={{ position: "absolute", width: size, height: size, ...pos }} />;
  const b = `${thickness}px solid ${color}`;
  return (
    <motion.span layoutId={layoutId} transition={{ type: "spring", stiffness: 500, damping: 40, mass: 0.6 }} style={{ position: "absolute", inset, pointerEvents: "none", zIndex: 3 }} aria-hidden>
      {c({ top: 0, left: 0, borderTop: b, borderLeft: b })}{c({ top: 0, right: 0, borderTop: b, borderRight: b })}
      {c({ bottom: 0, left: 0, borderBottom: b, borderLeft: b })}{c({ bottom: 0, right: 0, borderBottom: b, borderRight: b })}
    </motion.span>);
};
export const LogoReticle = () => <span style={{ position: "relative", width: 12, height: 12, display: "block" }}><Reticle size={4} thickness={1.5} inset={0} layoutId="logo" /></span>;
