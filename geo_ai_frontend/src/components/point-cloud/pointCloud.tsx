import React from "react";
import * as THREE from "three";

export const PointCloud: React.FC<{ object: THREE.Points }> = ({ object }) => {
  const box = new THREE.Box3().setFromObject(object);
  const center = new THREE.Vector3();
  box.getCenter(center);
  object.position.sub(center);
  object.rotation.x = -Math.PI / 2;

  return <primitive object={object}></primitive>;
};
