import type { DimMeta, DishPoint } from "../../contract";
import { DishVisual } from "./DishVisual";
import { topLabels } from "./sensory";

export function DishCard({
  dish,
  dims,
  onClick,
  compact,
}: {
  dish: DishPoint;
  dims?: DimMeta[];
  onClick?: () => void;
  compact?: boolean;
}) {
  const tags = topLabels(dish.vector, dims, compact ? 2 : 3);
  const className = `food-card ${compact ? "compact" : ""}`;
  const body = (
    <>
      <DishVisual dish={dish} />
      <div className="food-card-body">
        <h4>{dish.name}</h4>
        <p className="cuisine-line">{dish.cuisine}</p>
        {tags.length > 0 && <p className="taste-line">{tags.join(" · ")}</p>}
        {!compact && dish.blurb && <p className="blurb">{dish.blurb}</p>}
      </div>
    </>
  );
  if (onClick) {
    return (
      <button type="button" className={className} onClick={onClick}>
        {body}
      </button>
    );
  }
  return <div className={className}>{body}</div>;
}

export function TasteTags({ labels }: { labels: string[] }) {
  if (!labels.length) return null;
  return <p className="taste-line">{labels.join(" · ")}</p>;
}
