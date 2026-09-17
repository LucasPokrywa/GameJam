import React from "react";
import { Composition, Folder } from "remotion";
import "./index.css";
import { Trailer } from "./Trailer";
import { Ouverture } from "./scenes/Ouverture";
import { Regle } from "./scenes/Regle";
import { Mur } from "./scenes/Mur";
import { Os } from "./scenes/Os";
import { Radeau } from "./scenes/Radeau";
import { Autel } from "./scenes/Autel";
import { Titre } from "./scenes/Titre";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Trailer"
        component={Trailer}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
      />
      <Folder name="Scenes">
        <Composition
          id="Ouverture"
          component={Ouverture}
          durationInFrames={130}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Regle"
          component={Regle}
          durationInFrames={155}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Mur"
          component={Mur}
          durationInFrames={115}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Os"
          component={Os}
          durationInFrames={115}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Radeau"
          component={Radeau}
          durationInFrames={115}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Autel"
          component={Autel}
          durationInFrames={162}
          fps={30}
          width={1920}
          height={1080}
        />
        <Composition
          id="Titre"
          component={Titre}
          durationInFrames={180}
          fps={30}
          width={1920}
          height={1080}
        />
      </Folder>
    </>
  );
};
