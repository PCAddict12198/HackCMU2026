import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import * as THREE from "three";
import type { DishPoint, RecipeResponse, Vec3 } from "../../contract";
import { asTriple } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { cuisineColor } from "./colors";
import { topLabels } from "../dish/sensory";

const LIME = "#D8F25A";
const TERRACOTTA = "#C45C3E";
const MAP_BG = "#F3EEE3";
const MUTED = new THREE.Color("#C9C2B6");

function labelAnchor(xyz: Vec3, lift: number): [number, number, number] {
  return [xyz[0], xyz[1] + lift, xyz[2]];
}

function DishLabel({
  xyz,
  lift,
  children,
}: {
  xyz: Vec3;
  lift: number;
  children: ReactNode;
}) {
  return (
    <Html position={labelAnchor(xyz, lift)} distanceFactor={16} style={{ pointerEvents: "none" }}>
      <div className="star-label-wrap" style={{ transform: "translate(-50%, calc(-100% - 18px))" }}>
        {children}
      </div>
    </Html>
  );
}

function StarField({
  dishes,
  selectedId,
  highlightIds,
  twinHighlight,
  faded,
}: {
  dishes: DishPoint[];
  selectedId: string | null;
  highlightIds: string[];
  twinHighlight: string | null;
  faded: Set<string> | null;
}) {
  const select = useStore((s) => s.select);
  const space = useStore((s) => s.space);
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
      let s = d.tier === "extended" ? 0.7 : 1;
      const dimmed = faded?.has(d.id) ?? false;
      if (d.id === selectedId) s *= 1.85;
      else if (d.id === twinHighlight) s *= 1.45;
      else if (hi.has(d.id)) s *= 1.28;
      else if (dimmed) s *= 0.5;
      if (hover === i) s *= dimmed ? 1.45 : 1.12;
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
      color.set(cuisineColor(d.cuisine));
      if (dimmed && hover !== i) color.lerp(MUTED, 0.82);
      m.setColorAt(i, color);
    });
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  }, [color, dishes, dummy, faded, hi, hover, selectedId, twinHighlight]);

  const hoverDish = hover != null ? dishes[hover] : null;
  const selectedDish = selectedId ? dishes.find((d) => d.id === selectedId) : null;
  const tagsFor = (d: DishPoint) => topLabels(d.vector, space?.dims, 3);
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
        <sphereGeometry args={[0.32, segs, segs]} />
        <meshStandardMaterial roughness={0.22} metalness={0.08} toneMapped={false} />
      </instancedMesh>
      {selectedDish && selectedDish.id !== hoverDish?.id && (
        <DishLabel xyz={selectedDish.xyz} lift={1.35}>
          <div className="star-label">
            {selectedDish.name}
            <span className="sub">{selectedDish.cuisine}</span>
          </div>
        </DishLabel>
      )}
      {hoverDish && (
        <DishLabel xyz={hoverDish.xyz} lift={hoverDish.id === selectedId ? 1.35 : 1.05}>
          <div className="star-label">
            {hoverDish.name}
            <span className="sub">
              {hoverDish.cuisine}
              {tagsFor(hoverDish).length ? ` · ${tagsFor(hoverDish).join(" · ")}` : ""}
            </span>
          </div>
        </DishLabel>
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
        <sphereGeometry args={[0.48, 28, 28]} />
        <meshBasicMaterial color={LIME} transparent opacity={0.28} depthWrite={false} toneMapped={false} />
      </mesh>
    );
  });
}

function NeighborLinks({
  dishes,
  selectedId,
  ids,
}: {
  dishes: DishPoint[];
  selectedId: string | null;
  ids: string[];
}) {
  const from = dishes.find((d) => d.id === selectedId);
  if (!from) return null;
  const byId = new Map(dishes.map((d) => [d.id, d]));
  return [...new Set(ids)].map((id) => {
    const to = byId.get(id);
    if (!to) return null;
    return (
      <Line
        key={id}
        points={[asTriple(from.xyz), asTriple(to.xyz)]}
        color={cuisineColor(to.cuisine)}
        lineWidth={1.6}
        transparent
        opacity={0.55}
      />
    );
  });
}

function RecipeStar({ recipe }: { recipe: RecipeResponse }) {
  const pulse = useRef<THREE.Mesh>(null);
  const setRecipeStar = useStore((s) => s.setRecipeStar);
  useFrame((state) => {
    if (!pulse.current) return;
    const s = 1 + 0.06 * Math.sin(state.clock.elapsedTime * 1.6);
    pulse.current.scale.setScalar(s);
  });
  return (
    <mesh ref={pulse} position={asTriple(recipe.xyz)}>
      <sphereGeometry args={[0.4, 32, 32]} />
      <meshStandardMaterial color={LIME} roughness={0.25} metalness={0.1} toneMapped={false} />
      <Html position={[0, 1.35, 0]} distanceFactor={14} style={{ pointerEvents: "none" }}>
        <div className="star-label-wrap">
          <div className="star-label recipe">
            <span>{recipe.name}</span>
            <button
              type="button"
              className="star-dismiss"
              aria-label="Remove recipe from Taste Map"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                setRecipeStar(null);
              }}
            >
              ×
            </button>
          </div>
        </div>
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
  const trailLine = useMemo(() => new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xc45c3e })), [geo]);
  const goal = useMemo(() => new THREE.Vector3(to[0], to[1], to[2]), [to[0], to[1], to[2]]);
  const dashPts = useMemo(
    () => [new THREE.Vector3(from[0], from[1], from[2]), new THREE.Vector3(to[0], to[1], to[2])],
    [from, to],
  );

  useLayoutEffect(() => {
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
      <Line points={dashPts} color={TERRACOTTA} lineWidth={1.8} dashed dashSize={0.28} gapSize={0.18} />
      <mesh ref={marker} position={asTriple(to)}>
        <sphereGeometry args={[0.22, 24, 24]} />
        <meshStandardMaterial color={TERRACOTTA} roughness={0.25} metalness={0.08} toneMapped={false} />
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
          <Line points={[[0, 0, 0], p]} color="#D4CBBA" lineWidth={1} />
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
  const lastFocusKey = useRef("");
  const chasing = useRef<"focus" | "home" | null>(null);
  const homeCam = useMemo(() => new THREE.Vector3(0, 0, 36), []);
  const origin = useMemo(() => new THREE.Vector3(0, 0, 0), []);
  const goal = useRef(new THREE.Vector3());
  const camGoal = useRef(new THREE.Vector3());

  useFrame((_, dt) => {
    if (!controls) return;
    const k = 1 - Math.exp(-3.2 * dt);
    if (homeTick !== lastHome.current) {
      lastHome.current = homeTick;
      chasing.current = "home";
      lastFocusKey.current = "";
    }
    const focusKey = focus ? focus.join(",") : "";
    if (focusKey && focusKey !== lastFocusKey.current) {
      lastFocusKey.current = focusKey;
      chasing.current = "focus";
    }
    if (chasing.current === "home") {
      camera.position.lerp(homeCam, k);
      controls.target.lerp(origin, k);
      if (camera.position.distanceTo(homeCam) < 0.2) chasing.current = null;
    } else if (chasing.current === "focus" && focus) {
      goal.current.set(focus[0], focus[1], focus[2]);
      controls.target.lerp(goal.current, k);
      camGoal.current.set(focus[0] + 6, focus[1] + 4, focus[2] + 16);
      camera.position.lerp(camGoal.current, k * 0.85);
      if (camera.position.distanceTo(camGoal.current) < 0.25) chasing.current = null;
    }
    controls.update?.();
  });
  return null;
}

export function Galaxy({ cuisineFilter }: { cuisineFilter: string | null }) {
  const space = useStore((s) => s.space);
  const selectedId = useStore((s) => s.selectedId);
  const highlightIds = useStore((s) => s.highlightIds);
  const twinHighlight = useStore((s) => s.twinHighlight);
  const shiftResult = useStore((s) => s.shiftResult);
  const recipeStar = useStore((s) => s.recipeStar);
  const focus = useStore((s) => s.focus);
  const homeTick = useStore((s) => s.homeTick);
  const select = useStore((s) => s.select);
  const selected = useDish(selectedId);
  const pointerDown = useRef<{ x: number; y: number } | null>(null);

  const faded = useMemo(() => {
    if (!space) return null;
    const keep = new Set<string>();
    if (selectedId) keep.add(selectedId);
    if (twinHighlight) keep.add(twinHighlight);
    for (const id of highlightIds) keep.add(id);
    if (shiftResult && shiftResult.source_id === selectedId) {
      for (const r of shiftResult.results) keep.add(r.dish_id);
    }
    if (recipeStar) {
      for (const n of recipeStar.neighbors) keep.add(n.dish_id);
    }
    const set = new Set<string>();
    for (const d of space.dishes) {
      const filtered = !!cuisineFilter && d.cuisine !== cuisineFilter;
      const unfocused = !cuisineFilter && !!selectedId && !keep.has(d.id);
      if (filtered || unfocused) set.add(d.id);
    }
    return set.size ? set : null;
  }, [space, cuisineFilter, selectedId, highlightIds, twinHighlight, shiftResult, recipeStar]);

  if (!space) return <div className="galaxy-empty">Finding dishes…</div>;

  const haloIds = [...highlightIds, twinHighlight, selectedId].filter((x): x is string => !!x);
  const linkIds = [...highlightIds, twinHighlight].filter((x): x is string => !!x && x !== selectedId);
  if (shiftResult && shiftResult.source_id === selectedId) {
    for (const r of shiftResult.results) if (!linkIds.includes(r.dish_id)) linkIds.push(r.dish_id);
  }
  const large = space.dishes.length > 40;

  return (
    <Canvas
      camera={{ position: [0, 0, large ? 38 : 32], fov: 46 }}
      dpr={[1, 2]}
      gl={{ antialias: true, powerPreference: "high-performance", alpha: false, toneMapping: THREE.NoToneMapping }}
      onPointerDown={(e) => {
        pointerDown.current = { x: e.clientX, y: e.clientY };
      }}
      onPointerMissed={(e) => {
        const start = pointerDown.current;
        pointerDown.current = null;
        if (!start) return;
        const dx = e.clientX - start.x;
        const dy = e.clientY - start.y;
        if (dx * dx + dy * dy > 36) return;
        select(null);
      }}
    >
      <color attach="background" args={[MAP_BG]} />
      <fog attach="fog" args={[MAP_BG, 42, 88]} />
      <hemisphereLight args={["#FFFDF8", "#E8DCC8", 1.05]} />
      <ambientLight intensity={0.72} />
      <directionalLight position={[10, 14, 8]} intensity={1.15} color="#fffaf0" />
      <pointLight position={[-8, 6, 10]} intensity={0.45} color="#FFE8A0" />
      <StarField
        dishes={space.dishes}
        selectedId={selectedId}
        highlightIds={highlightIds}
        twinHighlight={twinHighlight}
        faded={faded}
      />
      <NeighborLinks dishes={space.dishes} selectedId={selectedId} ids={linkIds} />
      <Halos dishes={space.dishes} ids={haloIds} />
      {recipeStar && <RecipeStar recipe={recipeStar} />}
      {shiftResult && selected && shiftResult.source_id === selected.id && (
        <TargetGlide from={selected.xyz} to={shiftResult.target_xyz} trail={!large} />
      )}
      <Axes labels={space.pca.axis_labels} />
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.12}
        autoRotate={!focus}
        autoRotateSpeed={0.28}
        minDistance={6}
        maxDistance={110}
      />
      <CameraRig focus={focus} homeTick={homeTick} />
    </Canvas>
  );
}

export function CuisineLegend({
  active,
  onToggle,
}: {
  active: string | null;
  onToggle: (id: string | null) => void;
}) {
  const space = useStore((s) => s.space);
  if (!space) return null;
  const present = new Set(space.dishes.map((d) => d.cuisine));
  return (
    <div className="legend">
      {space.cuisines
        .filter((c) => present.has(c.id))
        .map((c) => (
          <button
            key={c.id}
            type="button"
            className={`legend-item ${active === c.id ? "active" : ""}`}
            onClick={() => onToggle(active === c.id ? null : c.id)}
          >
            <i style={{ background: cuisineColor(c.id) }} />
            {c.name}
          </button>
        ))}
    </div>
  );
}

export function MapFilters({
  query,
  onQuery,
  onPick,
}: {
  query: string;
  onQuery: (q: string) => void;
  onPick: (id: string) => void;
}) {
  const space = useStore((s) => s.space);
  const hits = space && query.trim() ? space.dishes.filter((d) => d.name.toLowerCase().includes(query.toLowerCase())).slice(0, 6) : [];
  return (
    <div className="map-filters">
      <input
        className="find"
        value={query}
        onChange={(e) => onQuery(e.target.value)}
        placeholder="Find a dish"
        aria-label="Find a dish"
      />
      {hits.length > 0 && (
        <div className="filter-row">
          {hits.map((d) => (
            <button key={d.id} type="button" onClick={() => onPick(d.id)}>
              {d.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
