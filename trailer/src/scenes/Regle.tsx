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

const { fontFamily } = loadFont();

/** The one rule the whole game is built on, straight from the tutorial text. */
export const Regle: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <AbsoluteFill
        style={{
          filter: "blur(5px) brightness(0.3) saturate(0.6)",
          scale: interpolate(frame, [0, 155], [1.02, 1.12], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
            output: "perceptual-scale",
          }),
        }}
      >
        <RoomStage room="level3" zoom={8.2} focusX={128} focusY={184}>
          <Sprite src="empaled.png" size={64} x={104} y={200} />
        </RoomStage>
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(11,9,8,0.35) 0%, rgba(11,9,8,0.95) 70%)",
        }}
      />

      <Interactive.Div
        name="Rule line 1"
        style={{
          position: "absolute",
          left: 142,
          top: 300,
          fontFamily,
          fontSize: 86,
          color: "#EDE6D6",
          opacity: interpolate(frame, [8, 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        LA FACON
      </Interactive.Div>

      <Interactive.Div
        name="Rule line 2"
        style={{
          position: "absolute",
          left: 142,
          top: 420,
          fontFamily,
          fontSize: 86,
          color: "#EDE6D6",
          opacity: interpolate(frame, [26, 38], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        DONT TU MEURS
      </Interactive.Div>

      <Interactive.Div
        name="Rule line 3"
        style={{
          position: "absolute",
          left: 142,
          top: 540,
          fontFamily,
          fontSize: 86,
          color: "#EDE6D6",
          opacity: interpolate(frame, [44, 56], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        DECIDE DE CE QUE
      </Interactive.Div>

      <Interactive.Div
        name="Rule line 4"
        style={{
          position: "absolute",
          left: 142,
          top: 660,
          fontFamily,
          fontSize: 86,
          color: "#9C1614",
          textShadow: "0 0 60px rgba(156,22,20,0.55)",
          opacity: interpolate(frame, [62, 76], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        DEVIENT TON CORPS
      </Interactive.Div>
    </AbsoluteFill>
  );
};
