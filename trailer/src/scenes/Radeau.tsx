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

/** Round 1's river: the only bridge across it is the one you drown to build. */
export const Radeau: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <RoomStage room="tuto" zoom={7.5} focusX={128} focusY={150}>
        {/* First life: walks straight into the river */}
        <Sprite
          src="run_up.png"
          size={64}
          cols={6}
          col={Math.floor(frame / 4) % 6}
          x={54}
          y={interpolate(frame, [0, 36], [206, 158], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          style={{
            opacity: interpolate(frame, [28, 36], [1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />

        {/* The RAFT corpse a DROWNING leaves, floating on its tile */}
        <Sprite
          src="corpse_water.png"
          size={16}
          x={54}
          y={158}
          style={{
            opacity: frame < 34 ? 0 : 1,
            scale: interpolate(frame, [34, 44], [2.2, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
            translate: `0px ${Math.sin(frame / 7) * 0.7}px`,
          }}
        />

        {/* Second life: crosses on it, then stands on the far bank */}
        <Sprite
          src={frame < 100 ? "run_up.png" : "idle_up.png"}
          size={64}
          cols={frame < 100 ? 6 : 8}
          col={frame < 100 ? Math.floor(frame / 4) % 6 : Math.floor(frame / 5) % 8}
          x={54}
          y={interpolate(frame, [46, 74, 100], [210, 168, 126], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          style={{ opacity: frame >= 46 ? 1 : 0 }}
        />
      </RoomStage>

      {/* Water swallowing the first one */}
      <AbsoluteFill
        style={{
          backgroundColor: "#2A6FA8",
          mixBlendMode: "screen",
          opacity: interpolate(frame, [30, 34, 46], [0, 0.5, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      <MecaniqueLabel
        cause="MORT NOYE"
        payoff="TON CORPS FAIT PONT"
        causeAt={38}
        payoffAt={50}
      />

      <DeathCounter count={frame < 34 ? 3 : 4} />
    </AbsoluteFill>
  );
};
