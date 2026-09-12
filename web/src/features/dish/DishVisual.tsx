import type { DishPoint } from "../../contract";
import { plateColors } from "../galaxy/colors";

function mix(id: string): number {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) h = Math.imul(h ^ id.charCodeAt(i), 16777619);
  return (h >>> 0) / 2 ** 32;
}

export function DishVisual({ dish, className }: { dish: DishPoint; className?: string }) {
  const [a, b, c] = plateColors(dish.cuisine);
  const n = mix(dish.id);
  const rot = Math.round(n * 40 - 12);
  return (
    <div className={`dish-visual ${className ?? ""}`} aria-hidden="true" style={{ background: c }}>
      <span className="plate" style={{ background: `radial-gradient(circle at 35% 30%, ${a}, ${b} 55%, ${c})` }}>
        <i style={{ transform: `translate(-12%, -8%) rotate(${rot}deg)`, background: a }} />
        <i style={{ transform: `translate(18%, 10%) rotate(${-rot}deg)`, background: b }} />
        <i className="glaze" />
      </span>
    </div>
  );
}
