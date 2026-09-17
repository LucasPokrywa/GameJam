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

/** Round 1: a zombie kill leaves bones, and bones are the only weapon there is. */
export const Os: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <RoomStage room="level1" zoom={7.5} focusX={128} focusY={184}>
        {/* The zombie closes in, then dies on the bones it created */}
        <Sprite
          src="zombie.png"
          size={32}
          cols={8}
          rows={4}
          col={
            (frame < 22 || (frame >= 38 && frame < 58))
              ? Math.floor(
                  interpolate(frame, [0, 22, 38, 58], [0, 28, 28, 44], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                    easing: Easing.linear,
                  }) / 3.5,
                ) % 8
              : 0
          }
          row={frame < 38 ? 3 : 1}
          x={interpolate(frame, [0, 22, 38, 58], [152, 124, 124, 140], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          y={196}
          style={{
            opacity: interpolate(frame, [92, 104], [1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            filter: `saturate(${interpolate(frame, [90, 96], [1, 6], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })})`,
            scale: interpolate(frame, [92, 104], [1, 0.2], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />

        {/* First life: caught in the open */}
        <Sprite
          src="idle_down.png"
          size={64}
          cols={8}
          col={Math.floor(frame / 5) % 8}
          x={100}
          y={198}
          style={{ opacity: frame < 22 ? 1 : 0 }}
        />

        {/* Bones, the corpse a ZOMBIE death leaves */}
        <Sprite
          src="bones.png"
          size={16}
          x={100}
          y={198}
          style={{
            opacity: frame < 22 || frame > 62 ? 0 : 1,
            scale: interpolate(frame, [22, 32], [2.4, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />

        {/* Second life: runs for the bones */}
        <Sprite
          src="run_side.png"
          size={64}
          cols={6}
          col={Math.floor(frame / 4) % 6}
          x={interpolate(frame, [34, 62], [44, 96], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          y={200}
          style={{ opacity: frame >= 34 && frame < 62 ? 1 : 0 }}
        />

        {/* Same body, now wearing the bones: the reinforced sprite */}
        <Sprite
          src={frame < 92 ? "run_side_armed.png" : "idle_side_armed.png"}
          size={64}
          cols={frame < 92 ? 6 : 8}
          col={frame < 92 ? Math.floor(frame / 4) % 6 : Math.floor(frame / 5) % 8}
          x={interpolate(frame, [62, 92], [96, 116], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          y={200}
          style={{ opacity: frame >= 62 ? 1 : 0 }}
        />
      </RoomStage>

      {/* Red on the death, gold on the pick-up */}
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
      <AbsoluteFill
        style={{
          backgroundColor: "#E8B646",
          mixBlendMode: "screen",
          opacity: interpolate(frame, [61, 64, 76], [0, 0.45, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      <MecaniqueLabel
        cause="MORT PAR ZOMBIE"
        payoff="TES OS FONT ARME"
        causeAt={28}
        payoffAt={40}
      />

      <DeathCounter count={frame < 22 ? 2 : 3} />
    </AbsoluteFill>
  );
};
