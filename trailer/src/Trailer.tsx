import React from "react";
import { AbsoluteFill, Audio, staticFile, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Ouverture } from "./scenes/Ouverture";
import { Regle } from "./scenes/Regle";
import { Mur } from "./scenes/Mur";
import { Os } from "./scenes/Os";
import { Radeau } from "./scenes/Radeau";
import { Autel } from "./scenes/Autel";
import { Titre } from "./scenes/Titre";

export const Trailer: React.FC = () => {
  const { fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={130} name="Ouverture">
          <Ouverture />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={155} name="Regle">
          <Regle />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={115} name="Mur">
          <Mur />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={115} name="Os">
          <Os />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={115} name="Radeau">
          <Radeau />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={162} name="Autel">
          <Autel />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={180} name="Titre">
          <Titre />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* Scanlines, so the 16 px artwork keeps its screen */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(to bottom, rgba(0,0,0,0.22) 0px, rgba(0,0,0,0.22) 1px, rgba(0,0,0,0) 1px, rgba(0,0,0,0) 3px)",
          opacity: 0.55,
          pointerEvents: "none",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.62) 100%)",
          pointerEvents: "none",
        }}
      />

      <Audio
        name="Main theme"
        src={staticFile("audio/main-theme.mp3")}
        trimBefore={8 * fps}
        volume={(f) =>
          f < fps
            ? (f / fps) * 0.62
            : f > durationInFrames - 2 * fps
              ? Math.max(0, (durationInFrames - f) / (2 * fps)) * 0.62
              : 0.62
        }
      />
    </AbsoluteFill>
  );
};
