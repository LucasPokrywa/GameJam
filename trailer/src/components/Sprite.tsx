import React from "react";
import { staticFile } from "remotion";

/**
 * One frame of a game spritesheet, positioned by its centre in room pixels.
 *
 * Sheets are laid out left to right (`col`) and, for the zombie, top to bottom
 * (`row`) — the same split `Entity.load_animation` does at runtime.
 */
export const Sprite: React.FC<{
  src: string;
  size: number;
  cols?: number;
  rows?: number;
  col?: number;
  row?: number;
  x: number;
  y: number;
  flip?: boolean;
  style?: React.CSSProperties;
}> = ({ src, size, cols = 1, rows = 1, col = 0, row = 0, x, y, flip, style }) => {
  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        backgroundImage: `url(${staticFile(`sprites/${src}`)})`,
        backgroundSize: `${cols * 100}% ${rows * 100}%`,
        backgroundPosition: `${cols > 1 ? (col / (cols - 1)) * 100 : 0}% ${
          rows > 1 ? (row / (rows - 1)) * 100 : 0
        }%`,
        imageRendering: "pixelated",
        scale: flip ? "-1 1" : "1 1",
        ...style,
      }}
    />
  );
};
