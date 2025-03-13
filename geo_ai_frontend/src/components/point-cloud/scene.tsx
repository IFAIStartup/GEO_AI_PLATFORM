import React from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls, Environment } from "@react-three/drei";
import { PCDLoader } from "three/addons/loaders/PCDLoader.js";

import { PointCloud } from "./pointCloud";

export const PointCloudScene: React.FC<{ path: string }> = ({ path }) => {
  const pcdObject = useLoader(
    PCDLoader,
    import.meta.env.VITE_SERVER_URL + "/" + path
  );

  return (
    <Canvas camera={{ position: [0, 100, 200] }}>
      <PointCloud object={pcdObject} />
      <OrbitControls zoomToCursor />
      <Environment preset="sunset" />
    </Canvas>
  );
};
