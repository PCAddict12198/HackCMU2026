import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { DishPoint, RecipeResponse, Vec3 } from "../../contract";
import { asTriple } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { cuisineColor } from "./colors";

function StarField({
  dishes,
  selectedId,
  highlightIds,
  twinHighlight,
}: {
  dishes: DishPoint[];
  selectedId: string | null;
  highlightIds: string[];
  twinHighlight: string | null;
}) {
  const select = useStore((s) => s.select);
  const mesh = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const color = useMemo(() => new THREE.Color(), []);
  const [hover, setHover] = useState<number | null>(null);
  const hi = useMemo(() => new Set(highlightIds), [highlightIds]);

  useLayoutEffect(() => {
    const m = mesh.current;
    if (!m) return;
    dishes.forEach((d, i) => {
      dummy.position.set(d.xyz[0], d.xyz[1], d.xyz[2]);
      let s = d.tier === "extended" ? 0.62 : 1;
      if (d.id === selectedId) s *= 1.9;
      else if (d.id === twinHighlight) s *= 1.55;
      else if (hi.has(d.id)) s *= 1.35;
      if (hover === i) s *= 1.2;
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
      color.set(cuisineColor(d.cuisine));
      m.setColorAt(i, color);
    });
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  }, [color, dishes, dummy, hi, hover, selectedId, twinHighlight]);

  const labelIdx = hover ?? dishes.findIndex((d) => d.id === selectedId);
  const label = labelIdx >= 0 ? dishes[labelIdx] : null;

  return (
    <>
      <instancedMesh
        ref={mesh}
        args={[undefined, undefined, dishes.length]}
        onClick={(e) => {
          e.stopPropagation();
          if (e.instanceId != null) select(dishes[e.instanceId].id);
        }}
        onPointerMove={(e) => {
          e.stopPropagation();
          if (e.instanceId != null) setHover(e.instanceId);
        }}
        onPointerOut={() => setHover(null)}
      >
        <sphereGeometry args={[0.22, 12, 12]} />
        <meshStandardMaterial vertexColors toneMapped={false} roughness={0.35} metalness={0.1} />
      </instancedMesh>
      {label && (
        <Html position={asTriple(label.xyz)} center distanceFactor={14} style={{ pointerEvents: "none" }}>
          <div className="star-label">{label.name}</div>
        </Html>
      )}
    </>
  );
}

function Halos({ dishes, ids }: { dishes: DishPoint[]; ids: string[] }) {
  const unique = [...new Set(ids.filter(Boolean))];
  return unique.map((id) => {
    const d = dishes.find((x) => x.id === id);
    if (!d) return null;
    return (
      <mesh key={id} position={asTriple(d.xyz)}>
        <sphereGeometry args={[0.48, 16, 16]} />
        <meshBasicMaterial color="#ffd166" transparent opacity={0.22} />
      </mesh>
    );
  });
}

function RecipeStar({ recipe }: { recipe: RecipeResponse }) {
  const pulse = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    if (!pulse.current) return;
    const s = 0.38 + 0.08 * Math.sin(state.clock.elapsedTime * 3);
    pulse.current.scale.setScalar(s / 0.38);
  });
  return (
    <mesh ref={pulse} position={asTriple(recipe.xyz)}>
      <sphereGeometry args={[0.38, 18, 18]} />
      <meshStandardMaterial color="#ffe8a3" emissive="#ffd166" emissiveIntensity={1.4} />
      <Html center distanceFactor={14} style={{ pointerEvents: "none" }}>
        <div className="star-label recipe">{recipe.name}</div>
      </Html>
    </mesh>
  );
}

function TargetGlide({ from, to }: { from: Vec3; to: Vec3 }) {
  const current = useRef(new THREE.Vector3(to[0], to[1], to[2]));
  const marker = useRef<THREE.Mesh>(null);
  const trail = useRef<[number, number, number][]>([asTriple(from)]);
  const [pts, setPts] = useState<[number, number, number][]>([asTriple(from), asTriple(to)]);
  const goal = useMemo(() => new THREE.Vector3(to[0], to[1], to[2]), [to[0], to[1], to[2]]);

  useEffect(() => {
    trail.current = [asTriple(from)];
    current.current.set(from[0], from[1], from[2]);
  }, [from]);

  useFrame((_, dt) => {
    current.current.lerp(goal, 1 - Math.exp(-5 * dt));
    const p: [number, number, number] = [current.current.x, current.current.y, current.current.z];
    if (marker.current) marker.current.position.set(...p);
    const last = trail.current[trail.current.length - 1];
    if (!last || Math.hypot(last[0] - p[0], last[1] - p[1], last[2] - p[2]) > 0.06) {
      trail.current = [...trail.current, p].slice(-32);
      setPts([asTriple(from), ...trail.current]);
    }
  });

  return (
    <>
      <Line points={pts} color="#ffd166" lineWidth={1.6} />
      <Line points={[asTriple(from), asTriple(to)]} color="#ffd166" lineWidth={1} dashed dashSize={0.28} gapSize={0.18} />
      <mesh ref={marker} position={asTriple(to)}>
        <sphereGeometry args={[0.3, 14, 14]} />
        <meshBasicMaterial color="#ffd166" wireframe />
      </mesh>
    </>
  );
}

function Axes({ labels }: { labels: string[] }) {
  const len = 11;
  const ends: [number, number, number][] = [
    [len, 0, 0],
    [0, len, 0],
    [0, 0, len],
  ];
  return (
    <group>
      {ends.map((p, i) => (
        <group key={labels[i] ?? i}>
          <Line points={[[0, 0, 0], p]} color="#2a3146" lineWidth={1} />
          <Html position={p} center style={{ pointerEvents: "none" }}>
            <div className="axis-label">{labels[i]}</div>
          </Html>
        </group>
      ))}
    </group>
  );
}

function CameraRig({ focus, homeTick }: { focus: Vec3 | null; homeTick: number }) {
  const { camera } = useThree();
  const controls = useThree((s) => s.controls) as { target: THREE.Vector3; update?: () => void } | null;
  const lastHome = useRef(homeTick);
  const homeCam = useMemo(() => new THREE.Vector3(0, 0, 26), []);
  const origin = useMemo(() => new THREE.Vector3(0, 0, 0), []);
  const goal = useRef(new THREE.Vector3());

  useFrame((_, dt) => {
    if (!controls) return;
    const k = 1 - Math.exp(-3.2 * dt);
    if (homeTick !== lastHome.current) {
      lastHome.current = homeTick;
    }
    const resetting = homeTick > 0 && !focus;
    if (resetting) {
      camera.position.lerp(homeCam, k);
      controls.target.lerp(origin, k);
    } else if (focus) {
      goal.current.set(focus[0], focus[1], focus[2]);
      controls.target.lerp(goal.current, k);
    }
    controls.update?.();
  });
  return null;
}

export function Galaxy() {
  const space = useStore((s) => s.space);
  const selectedId = useStore((s) => s.selectedId);
  const highlightIds = useStore((s) => s.highlightIds);
  const twinHighlight = useStore((s) => s.twinHighlight);
  const shiftResult = useStore((s) => s.shiftResult);
  const recipeStar = useStore((s) => s.recipeStar);
  const focus = useStore((s) => s.focus);
  const homeTick = useStore((s) => s.homeTick);
  const selected = useDish(selectedId);

  if (!space) return <div className="galaxy-empty">Loading TasteSpace...</div>;

  const haloIds = [...highlightIds, twinHighlight, selectedId].filter((x): x is string => !!x);

  return (
    <Canvas camera={{ position: [0, 0, 26], fov: 50 }}>
      <color attach="background" args={["#05060a"]} />
      <ambientLight intensity={0.55} />
      <pointLight position={[18, 18, 22]} intensity={1.15} />
      <StarField
        dishes={space.dishes}
        selectedId={selectedId}
        highlightIds={highlightIds}
        twinHighlight={twinHighlight}
      />
      <Halos dishes={space.dishes} ids={haloIds} />
      {recipeStar && <RecipeStar recipe={recipeStar} />}
      {shiftResult && selected && shiftResult.source_id === selected.id && (
        <TargetGlide from={selected.xyz} to={shiftResult.target_xyz} />
      )}
      <Axes labels={space.pca.axis_labels} />
      <OrbitControls makeDefault enableDamping autoRotate={!selectedId} autoRotateSpeed={0.35} />
      <CameraRig focus={focus} homeTick={homeTick} />
    </Canvas>
  );
}

export function CuisineLegend() {
  const space = useStore((s) => s.space);
  if (!space) return null;
  const present = new Set(space.dishes.map((d) => d.cuisine));
  return (
    <div className="legend">
      {space.cuisines
        .filter((c) => present.has(c.id))
        .map((c) => (
          <span key={c.id} className="legend-item">
            <i style={{ background: cuisineColor(c.id) }} />
            {c.name}
          </span>
        ))}
    </div>
  );
}
