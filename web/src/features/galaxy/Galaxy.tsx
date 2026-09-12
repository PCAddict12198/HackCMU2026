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

  const segs = dishes.length > 40 ? 24 : 36;
  return (
    <>
      <instancedMesh
        key={`${dishes.length}-${segs}`}
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
        <sphereGeometry args={[0.3, segs, segs]} />
        <meshStandardMaterial roughness={0.22} metalness={0.28} envMapIntensity={0.9} />
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
  const byId = useMemo(() => new Map(dishes.map((d) => [d.id, d])), [dishes]);
  const unique = [...new Set(ids.filter(Boolean))].slice(0, 8);
  return unique.map((id) => {
    const d = byId.get(id);
    if (!d) return null;
    return (
      <mesh key={id} position={asTriple(d.xyz)}>
        <sphereGeometry args={[0.52, 32, 32]} />
        <meshBasicMaterial color="#e4c08a" transparent opacity={0.16} depthWrite={false} />
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
      <sphereGeometry args={[0.4, 36, 36]} />
      <meshStandardMaterial color="#ffe8a3" emissive="#e4c08a" emissiveIntensity={0.85} roughness={0.18} metalness={0.35} />
      <Html center distanceFactor={14} style={{ pointerEvents: "none" }}>
        <div className="star-label recipe">{recipe.name}</div>
      </Html>
    </mesh>
  );
}

function TargetGlide({ from, to, trail }: { from: Vec3; to: Vec3; trail: boolean }) {
  const current = useRef(new THREE.Vector3(to[0], to[1], to[2]));
  const last = useRef(new THREE.Vector3(from[0], from[1], from[2]));
  const marker = useRef<THREE.Mesh>(null);
  const count = useRef(1);
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(96), 3));
    g.setDrawRange(0, 2);
    return g;
  }, []);
  const trailLine = useMemo(() => new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xe4c08a })), [geo]);
  const goal = useMemo(() => new THREE.Vector3(to[0], to[1], to[2]), [to[0], to[1], to[2]]);
  const dashPts = useMemo(
    () => [new THREE.Vector3(from[0], from[1], from[2]), new THREE.Vector3(to[0], to[1], to[2])],
    [from, to],
  );

  useEffect(() => {
    current.current.set(from[0], from[1], from[2]);
    last.current.set(from[0], from[1], from[2]);
    count.current = 1;
    const pos = geo.getAttribute("position") as THREE.BufferAttribute;
    pos.setXYZ(0, from[0], from[1], from[2]);
    pos.needsUpdate = true;
  }, [from, geo]);

  useFrame((_, dt) => {
    current.current.lerp(goal, 1 - Math.exp(-5 * dt));
    if (marker.current) marker.current.position.copy(current.current);
    if (!trail) return;
    if (last.current.distanceTo(current.current) < 0.08) return;
    last.current.copy(current.current);
    const pos = geo.getAttribute("position") as THREE.BufferAttribute;
    const i = Math.min(count.current, 31);
    pos.setXYZ(i, current.current.x, current.current.y, current.current.z);
    if (count.current < 31) count.current += 1;
    pos.needsUpdate = true;
    geo.setDrawRange(0, Math.max(count.current, 2));
  });

  return (
    <>
      {trail && <primitive object={trailLine} />}
      <Line points={dashPts} color="#e4c08a" lineWidth={1.4} dashed dashSize={0.28} gapSize={0.18} />
      <mesh ref={marker} position={asTriple(to)}>
        <sphereGeometry args={[0.26, 32, 32]} />
        <meshStandardMaterial color="#e4c08a" emissive="#e4c08a" emissiveIntensity={0.55} roughness={0.2} metalness={0.4} wireframe={false} />
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
          <Line points={[[0, 0, 0], p]} color="#3a342c" lineWidth={1} />
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
  const homeCam = useMemo(() => new THREE.Vector3(0, 0, 34), []);
  const origin = useMemo(() => new THREE.Vector3(0, 0, 0), []);
  const goal = useRef(new THREE.Vector3());
  const camGoal = useRef(new THREE.Vector3());

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
      camGoal.current.set(focus[0] + 5, focus[1] + 3.5, focus[2] + 11);
      camera.position.lerp(camGoal.current, k * 0.85);
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

  const large = space.dishes.length > 40;

  return (
    <Canvas
      camera={{ position: [0, 0, large ? 34 : 26], fov: 46 }}
      dpr={[1, 2]}
      gl={{ antialias: true, powerPreference: "high-performance", alpha: false }}
    >
      <color attach="background" args={["#05040a"]} />
      <fog attach="fog" args={["#05040a", 22, 58]} />
      <hemisphereLight args={["#f0e6d4", "#1a1210", 0.55]} />
      <directionalLight position={[10, 14, 8]} intensity={1.35} color="#fff6ea" />
      <pointLight position={[-12, -4, 10]} intensity={0.55} color="#c4a0ff" />
      <pointLight position={[4, 8, -10]} intensity={0.28} color="#e4c08a" />
      <StarField
        dishes={space.dishes}
        selectedId={selectedId}
        highlightIds={highlightIds}
        twinHighlight={twinHighlight}
      />
      <Halos dishes={space.dishes} ids={haloIds} />
      {recipeStar && <RecipeStar recipe={recipeStar} />}
      {shiftResult && selected && shiftResult.source_id === selected.id && (
        <TargetGlide from={selected.xyz} to={shiftResult.target_xyz} trail={!large} />
      )}
      <Axes labels={space.pca.axis_labels} />
      <OrbitControls makeDefault enableDamping dampingFactor={0.12} autoRotate={!selectedId} autoRotateSpeed={0.35} />
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
