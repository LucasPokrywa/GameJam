import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

/**
 * A level room from the game, drawn at `zoom` screen pixels per room pixel.
 *
 * The rooms in `public/rooms/` are the game's own 256x256 layers flattened in
 * the order `Level._load_level_scenery` stacks them, so children can be placed
 * with the very coordinates `levels.py` uses (origin top-left, y downwards).
 */
export const RoomStage: React.FC<{
  room: string;
  zoom: number;
  focusX: number;
  focusY: number;
  children?: React.ReactNode;
}> = ({ room, zoom, focusX, focusY, children }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0908", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 960 - focusX * zoom,
          top: 540 - focusY * zoom,
          width: 256,
          height: 256,
          scale: zoom,
          transformOrigin: "0 0",
        }}
      >
        <Img
          name="Room"
          src={staticFile(`rooms/${room}.png`)}
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: 256,
            height: 256,
            imageRendering: "pixelated",
          }}
        />
        {children}
      </div>
    </AbsoluteFill>
  );
};
