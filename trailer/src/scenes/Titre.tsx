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

/** Title card, in the poster's art direction: dark brick, bone cream, dark blood. */
export const Titre: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <AbsoluteFill style={{ filter: "brightness(0.5) saturate(0.55) blur(2px)" }}>
        <RoomStage
          room="level5"
          zoom={interpolate(frame, [0, 180], [24, 27], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          })}
          focusX={128}
          focusY={40}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 42%, rgba(120,10,10,0.3) 0%, rgba(11,9,8,0.9) 58%, rgba(11,9,8,1) 85%)",
        }}
      />

      <Interactive.Div
        name="Title"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 330,
          textAlign: "center",
          fontFamily,
          fontSize: 168,
          color: "#EDE6D6",
          textShadow:
            "0 0 90px rgba(156,22,20,0.75), 8px 8px 0 #6E0C0C, -8px 8px 0 #6E0C0C, 0 16px 0 #4A0808",
          opacity: interpolate(frame, [4, 14], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          scale: interpolate(frame, [4, 22], [1.22, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            output: "perceptual-scale",
          }),
        }}
      >
        MANY MEN
      </Interactive.Div>

      <Interactive.Div
        name="Tagline"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 620,
          textAlign: "center",
          fontFamily,
          fontSize: 50,
          letterSpacing: 2,
          color: "#9C1614",
          opacity: interpolate(frame, [30, 44], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        CHAQUE MORT EST UN OUTIL
      </Interactive.Div>

      {/* The hero, waiting for the next death */}
      <AbsoluteFill
        style={{
          opacity: interpolate(frame, [46, 62], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 960,
            top: 790,
            width: 0,
            height: 0,
          }}
        >
          <div style={{ position: "absolute", scale: 8, transformOrigin: "50% 50%" }}>
            <Sprite
              src="idle_down.png"
              size={64}
              cols={8}
              col={Math.floor(frame / 5) % 8}
              x={0}
              y={0}
            />
          </div>
        </div>
      </AbsoluteFill>

      <Interactive.Div
        name="Credits"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 92,
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          rowGap: 14,
          padding: "0 110px",
          textAlign: "center",
          fontFamily,
          fontSize: 24,
          lineHeight: 1.25,
          color: "#8E8578",
          opacity: interpolate(frame, [86, 100], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <span>CHAMSEDINE AMOUCHE</span>
        <span>LUCAS MEENS</span>
        <span>LUCAS POKRYWA</span>
        <span>LUCAS CRESPY</span>
        <span>AMELIA BEN YOUSSEF</span>
        <span>PIERRE GUEROULT</span>
      </Interactive.Div>

      {/* Out to black */}
      <AbsoluteFill
        style={{
          backgroundColor: "#000000",
          opacity: interpolate(frame, [160, 180], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.33, 0, 0.67, 1),
          }),
        }}
      />
    </AbsoluteFill>
  );
};
