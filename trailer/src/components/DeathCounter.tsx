import React from "react";
import { Interactive } from "remotion";
import { loadFont } from "@remotion/google-fonts/PressStart2P";

const { fontFamily } = loadFont();

/** The HUD counter from the game, ticking through the whole trailer. */
export const DeathCounter: React.FC<{ count: number }> = ({ count }) => {
  return (
    <Interactive.Div
      name="Death counter"
      style={{
        position: "absolute",
        left: 142,
        top: 96,
        fontFamily,
        fontSize: 40,
        letterSpacing: 4,
        color: "#EDE6D6",
        textShadow: "0 5px 0 #6E0C0C",
      }}
    >
      MORTS {String(count).padStart(2, "0")}
    </Interactive.Div>
  );
};
