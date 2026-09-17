import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Interactive,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/PressStart2P";
import { RoomStage } from "../components/RoomStage";
import { Sprite } from "../components/Sprite";

const { fontFamily } = loadFont();

const ROOMS = ["tuto", "puzzle1", "level3", "level4", "level5"];

/** The altar takes the bodies, the door opens, and the next room is worse. */
export const Autel: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908" }}>
      <Sequence name="Altar" durationInFrames={80}>
        <RoomStage room="level4" zoom={9} focusX={128} focusY={192}>
          <Sprite
            src={frame > 14 ? "slot_filled.png" : "slot_wall.png"}
            size={20}
            x={96}
            y={200}
            style={{
              scale: interpolate(frame, [14, 26], [1.6, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.bezier(0.16, 1, 0.3, 1),
                output: "perceptual-scale",
              }),
            }}
          />
          <Sprite
            src={frame > 36 ? "slot_filled.png" : "slot_bones.png"}
            size={20}
            x={120}
            y={200}
            style={{
              scale: interpolate(frame, [36, 48], [1.6, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.bezier(0.16, 1, 0.3, 1),
                output: "perceptual-scale",
              }),
            }}
          />
          <Sprite
            src={frame > 58 ? "slot_filled.png" : "slot_wall.png"}
            size={20}
            x={144}
            y={200}
            style={{
              scale: interpolate(frame, [58, 70], [1.6, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.bezier(0.16, 1, 0.3, 1),
                output: "perceptual-scale",
              }),
            }}
          />
          <Sprite
            src="idle_down_armed.png"
            size={64}
            cols={8}
            col={Math.floor(frame / 5) % 8}
            x={184}
            y={206}
          />
        </RoomStage>

        <AbsoluteFill
          style={{
            backgroundColor: "#E8B646",
            mixBlendMode: "screen",
            opacity: interpolate(
              frame,
              [14, 18, 28, 36, 40, 50, 58, 62, 74],
              [0, 0.22, 0, 0, 0.22, 0, 0, 0.34, 0],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              },
            ),
          }}
        />

        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: 340,
            background:
              "linear-gradient(to bottom, rgba(11,9,8,0) 0%, rgba(11,9,8,0.9) 55%, rgba(11,9,8,0.97) 100%)",
          }}
        />

        <Interactive.Div
          name="Altar line"
          style={{
            position: "absolute",
            left: 142,
            bottom: 140,
            fontFamily,
            fontSize: 74,
            color: "#EDE6D6",
            textShadow: "0 8px 0 #6E0C0C",
            opacity: interpolate(frame, [8, 20], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
          }}
        >
          NOURRIS L&apos;AUTEL
        </Interactive.Div>
      </Sequence>

      <Sequence name="Rooms" from={80} durationInFrames={82}>
        <AbsoluteFill
          style={{
            backgroundColor: "#0b0908",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {ROOMS.map((room, index) => (
            <Sequence
              key={room}
              name={room}
              from={index * 14}
              durationInFrames={14}
              layout="absolute-fill"
            >
              <AbsoluteFill
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Img
                  src={staticFile(`rooms/${room}.png`)}
                  style={{
                    width: 1040,
                    height: 1040,
                    imageRendering: "pixelated",
                    filter: "brightness(0.85)",
                    scale: interpolate(frame - 80 - index * 14, [0, 14], [1, 1.07], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                      easing: Easing.linear,
                      output: "perceptual-scale",
                    }),
                  }}
                />
              </AbsoluteFill>
            </Sequence>
          ))}
        </AbsoluteFill>

        <AbsoluteFill
          style={{
            background:
              "linear-gradient(to right, rgba(11,9,8,1) 0%, rgba(11,9,8,0) 16%, rgba(11,9,8,0) 84%, rgba(11,9,8,1) 100%), linear-gradient(to bottom, rgba(11,9,8,0) 62%, rgba(11,9,8,0.92) 88%, rgba(11,9,8,0.98) 100%)",
          }}
        />

        <Interactive.Div
          name="Rooms line"
          style={{
            position: "absolute",
            left: 142,
            bottom: 140,
            fontFamily,
            fontSize: 74,
            color: "#EDE6D6",
            textShadow: "0 8px 0 #6E0C0C",
            opacity: interpolate(frame, [84, 94], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
          }}
        >
          CINQ SALLES
        </Interactive.Div>
        <Interactive.Div
          name="Rooms line 2"
          style={{
            position: "absolute",
            left: 142,
            bottom: 60,
            fontFamily,
            fontSize: 44,
            color: "#9C1614",
            opacity: interpolate(frame, [96, 106], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
          }}
        >
          UNE SEULE SORTIE
        </Interactive.Div>
      </Sequence>
    </AbsoluteFill>
  );
};
