import React from "react";
import {
  AbsoluteFill,
  Easing,
  Interactive,
  interpolate,
  useCurrentFrame,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/PressStart2P";
import { RoomStage } from "../components/RoomStage";
import { Sprite } from "../components/Sprite";
import { DeathCounter } from "../components/DeathCounter";

const { fontFamily } = loadFont();

/** Round 3: the player walks up to the turret and takes an arrow. */
export const Ouverture: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <RoomStage
        room="level3"
        zoom={interpolate(frame, [0, 130], [7.5, 8.2], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.33, 0, 0.67, 1),
        })}
        focusX={128}
        focusY={196}
      >
        {/* The turret, drawn as the flame the game gives it */}
        <Sprite
          src="tower.png"
          size={16}
          cols={8}
          col={Math.floor(frame / 3) % 8}
          x={152}
          y={200}
          style={{
            scale: interpolate(frame, [44, 52, 62], [1, 1.9, 1.1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              output: "perceptual-scale",
            }),
          }}
        />

        {/* The arrow, already pointing left in the game's artwork */}
        <Sprite
          src="arrow.png"
          size={16}
          x={interpolate(frame, [52, 70], [144, 110], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          y={198}
          style={{
            opacity: interpolate(frame, [51, 52, 69, 70], [0, 1, 1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />

        {/* Alive: runs east towards the turret, then stops dead */}
        <Sprite
          src={frame < 40 ? "run_side.png" : "idle_side.png"}
          size={64}
          cols={frame < 40 ? 6 : 8}
          col={frame < 40 ? Math.floor(frame / 4) % 6 : Math.floor(frame / 5) % 8}
          x={interpolate(frame, [0, 40], [74, 104], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          })}
          y={200}
          style={{
            opacity: frame < 70 ? 1 : 0,
          }}
        />

        {/* Dead: the empaled sprite the game leaves on an arrow death */}
        <Sprite
          src="empaled.png"
          size={64}
          x={104}
          y={200}
          style={{
            opacity: frame < 70 ? 0 : 1,
          }}
        />
      </RoomStage>

      {/* Blood hit */}
      <AbsoluteFill
        style={{
          backgroundColor: "#9C1614",
          mixBlendMode: "screen",
          opacity: interpolate(frame, [69, 71, 84], [0, 0.72, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      />

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 380,
          background:
            "linear-gradient(to bottom, rgba(11,9,8,0) 0%, rgba(11,9,8,0.9) 55%, rgba(11,9,8,0.98) 100%)",
          opacity: interpolate(frame, [72, 84], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />

      <Interactive.Div
        name="Hook"
        style={{
          position: "absolute",
          left: 142,
          bottom: 150,
          fontFamily,
          fontSize: 110,
          whiteSpace: "nowrap",
          color: "#EDE6D6",
          textShadow: "0 12px 0 #6E0C0C",
          opacity: interpolate(frame, [80, 90], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [80, 94], ["0px 40px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        TU VAS MOURIR.
      </Interactive.Div>

      <DeathCounter count={frame < 70 ? 0 : 1} />
    </AbsoluteFill>
  );
};
