import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
} from "remotion";
import { RoomStage } from "../components/RoomStage";
import { Sprite } from "../components/Sprite";
import { DeathCounter } from "../components/DeathCounter";
import { MecaniqueLabel } from "../components/MecaniqueLabel";

/** Round 4: dying under the turret leaves the body that blinds it. */
export const Mur: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <RoomStage room="level4" zoom={7.5} focusX={128} focusY={128}>
        {/* Current game crossbow: idle pose, then firing when each arrow leaves. */}
        <Sprite
          src="arrow_tower.png"
          size={16}
          rows={2}
          row={(frame >= 4 && frame < 10) || (frame >= 54 && frame < 60) ? 1 : 0}
          x={120}
          y={68}
          style={{
            scale: interpolate(frame, [0, 6, 16, 44, 52, 62], [1.6, 1.1, 1, 1, 1.8, 1.1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />

        {/* First arrow: finds the player */}
        <Sprite
          src="arrow.png"
          size={16}
          x={120}
          y={interpolate(frame, [4, 22], [84, 142], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          style={{
            rotate: "-90deg",
            opacity: interpolate(frame, [3, 4, 21, 22], [0, 1, 1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />

        {/* Second arrow: stopped by the body left behind */}
        <Sprite
          src="arrow.png"
          size={16}
          x={120}
          y={interpolate(frame, [54, 70], [84, 134], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          style={{
            rotate: "-90deg",
            opacity: interpolate(frame, [53, 54, 69, 70], [0, 1, 1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />

        {/* The body stops the shot: a spark where the arrow breaks on it */}
        <div
          style={{
            position: "absolute",
            left: 112,
            top: 130,
            width: 16,
            height: 16,
            borderRadius: 16,
            backgroundColor: "#FFD98A",
            filter: "blur(3px)",
            opacity: interpolate(frame, [69, 72, 84], [0, 0.95, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />

        {/* Alive under the turret */}
        <Sprite
          src="idle_down.png"
          size={64}
          cols={8}
          col={Math.floor(frame / 5) % 8}
          x={120}
          y={148}
          style={{ opacity: frame < 22 ? 1 : 0 }}
        />

        {/* The corpse-wall, snapped to its tile like Level.spawn_corpse does */}
        <Sprite
          src="corpse.png"
          size={16}
          x={120}
          y={144}
          style={{
            opacity: frame < 22 ? 0 : 1,
            scale: interpolate(frame, [22, 32], [2.4, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />

      </RoomStage>

      <AbsoluteFill
        style={{
          backgroundColor: "#9C1614",
          mixBlendMode: "screen",
          opacity: interpolate(frame, [21, 23, 34], [0, 0.6, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      <MecaniqueLabel
        cause="MORT PAR FLECHE"
        payoff="TON CORPS FAIT MUR"
        causeAt={28}
        payoffAt={40}
      />

      <DeathCounter count={frame < 22 ? 1 : 2} />
    </AbsoluteFill>
  );
};
