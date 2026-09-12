// 3D Flavor Galaxy (baseline). P3 TODO: instanced stars, camera fly-to, smooth target glide,
// PCA axis labels, cluster halos. Positions come straight from the engine (DishPoint.xyz).
import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useState } from "react";
import type { DishPoint, Vec3 } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { cuisineColor } from "./colors";

function Star({ dish, selected, highlighted }: { dish: DishPoint; selected: boolean; highlighted: boolean }) {
  const select = useStore((s) => s.select);
  const [hover, setHover] = useState(false);
  const lit = selected || highlighted || hover;
  return (
    <mesh
      position={dish.xyz as unknown as [number, number, number]}
      onClick={(e) => {
        e.stopPropagation();
        select(dish.id);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHover(true);
      }}
      onPointerOut={() => setHover(false)}
    >
      <sphereGeometry args={[selected ? 0.45 : highlighted ? 0.34 : 0.22, 20, 20]} />
      <meshStandardMaterial
        color={cuisineColor(dish.cuisine)}
        emissive={cuisineColor(dish.cuisine)}
        emissiveIntensity={lit ? 0.9 : 0.2}
        transparent
        opacity={dish.tier === "extended" ? 0.45 : 1}
      />
      {lit && (
        <Html center distanceFactor={14} style={{ pointerEvents: "none" }}>
          <div className="star-label">{dish.name}</div>
        </Html>
      )}
    </mesh>
  );
}

function Target({ from, to }: { from: Vec3; to: Vec3 }) {
  const a = from as unknown as [number, number, number];
  const b = to as unknown as [number, number, number];
  return (
    <>
      <Line points={[a, b]} color="#ffd166" lineWidth={1.5} dashed dashSize={0.3} gapSize={0.2} />
      <mesh position={b}>
        <sphereGeometry args={[0.32, 16, 16]} />
        <meshBasicMaterial color="#ffd166" wireframe />
      </mesh>
    </>
  );
}

export function Galaxy() {
  const space = useStore((s) => s.space);
  const selectedId = useStore((s) => s.selectedId);
  const highlightIds = useStore((s) => s.highlightIds);
  const shiftResult = useStore((s) => s.shiftResult);
  const selected = useDish(selectedId);
  if (!space) return <div className="galaxy-empty">Loading TasteSpace...</div>;
  return (
    <Canvas camera={{ position: [0, 0, 26], fov: 50 }}>
      <color attach="background" args={["#05060a"]} />
      <ambientLight intensity={0.6} />
      <pointLight position={[20, 20, 20]} intensity={1.2} />
      {space.dishes.map((d) => (
        <Star key={d.id} dish={d} selected={d.id === selectedId} highlighted={highlightIds.includes(d.id)} />
      ))}
      {shiftResult && selected && shiftResult.source_id === selected.id && (
        <Target from={selected.xyz} to={shiftResult.target_xyz} />
      )}
      <OrbitControls enableDamping autoRotate={!selectedId} autoRotateSpeed={0.4} />
    </Canvas>
  );
}
