import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/PressStart2P";

const { fontFamily } = loadFont();

/** Lower third naming a death and what the body it leaves is good for. */
export const MecaniqueLabel: React.FC<{
  cause: string;
  payoff: string;
  causeAt: number;
  payoffAt: number;
}> = ({ cause, payoff, causeAt, payoffAt }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 340,
          background:
            "linear-gradient(to bottom, rgba(11,9,8,0) 0%, rgba(11,9,8,0.9) 55%, rgba(11,9,8,0.97) 100%)",
          opacity: interpolate(frame, [causeAt - 8, causeAt + 4], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 142,
          bottom: 252,
          fontFamily,
          fontSize: 52,
          letterSpacing: 2,
          color: "#9C1614",
          opacity: interpolate(frame, [causeAt, causeAt + 10], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {cause}
      </div>
      <div
        style={{
          position: "absolute",
          left: 142,
          bottom: 130,
          fontFamily,
          fontSize: 88,
          color: "#EDE6D6",
          textShadow: "0 9px 0 #6E0C0C",
          opacity: interpolate(frame, [payoffAt, payoffAt + 10], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(
            frame,
            [payoffAt, payoffAt + 14],
            ["0px 26px", "0px 0px"],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            },
          ),
        }}
      >
        {payoff}
      </div>
    </AbsoluteFill>
  );
};
