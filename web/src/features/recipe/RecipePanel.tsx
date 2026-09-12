import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Course, DishFormat } from "../../contract";
import { closerThan } from "../shared/copy";
import { useStore } from "../../state/store";
import { ErrorState, Loading } from "../shared/Status";
import { DishCard } from "../dish/DishCard";

const FORMATS: DishFormat[] = [
  "soup",
  "noodles",
  "rice_dish",
  "stew_braise",
  "fried",
  "grilled_roasted",
  "raw_salad",
  "bread_sandwich",
  "dumpling",
  "baked_sweet",
  "custard_creamy",
  "frozen",
];

export function RecipePanel() {
  const space = useStore((s) => s.space);
  const setRecipeStar = useStore((s) => s.setRecipeStar);
  const setPanel = useStore((s) => s.setPanel);
  const placeRecipeTick = useStore((s) => s.placeRecipeTick);
  const text = useStore((s) => s.recipeText);
  const course = useStore((s) => s.recipeCourse);
  const format = useStore((s) => s.recipeFormat);
  const data = useStore((s) => s.recipeMapped);
  const setRecipeText = useStore((s) => s.setRecipeText);
  const setRecipeCourse = useStore((s) => s.setRecipeCourse);
  const setRecipeFormat = useStore((s) => s.setRecipeFormat);
  const setRecipeMapped = useStore((s) => s.setRecipeMapped);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.recipe({
        text: useStore.getState().recipeText,
        course: useStore.getState().recipeCourse || null,
        format: useStore.getState().recipeFormat || null,
      });
      setRecipeMapped(res);
      setRecipeStar(res);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (placeRecipeTick > 0) void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [placeRecipeTick]);

  const showOnMap = () => {
    const mapped = useStore.getState().recipeMapped;
    if (mapped) setRecipeStar(mapped);
    setPanel("twins");
    window.dispatchEvent(new Event("tastespace:show-map"));
  };

  const dishOf = (id: string) => space?.dishes.find((d) => d.id === id);

  return (
    <div className="recipe-page">
      <h3 className="panel-title">Map my recipe</h3>
      <p className="lede-sm">Paste a recipe and see where it lives in TasteSpace.</p>
      <textarea
        rows={8}
        value={text}
        onChange={(e) => setRecipeText(e.target.value)}
        placeholder="Paste ingredients or a recipe here..."
      />
      <div className="row" style={{ margin: "12px 0" }}>
        <select value={course} onChange={(e) => setRecipeCourse(e.target.value as Course | "")}>
          <option value="">any meal</option>
          <option value="savory">savory</option>
          <option value="dessert">sweet</option>
        </select>
        <select value={format} onChange={(e) => setRecipeFormat(e.target.value as DishFormat | "")}>
          <option value="">any format</option>
          {FORMATS.map((f) => (
            <option key={f} value={f}>
              {f.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>
      <div className="recipe-actions">
        <button type="button" className="primary" onClick={() => void run()} disabled={busy}>
          {busy ? "Mapping…" : "Map this recipe"}
        </button>
        <button type="button" onClick={showOnMap} disabled={!data || busy}>
          Show on Taste Map
        </button>
      </div>
      {error != null && <ErrorState error={error} onRetry={() => void run()} />}
      {busy && <Loading label="Finding where this recipe lives…" />}
      {data && (
        <>
          <h4>Your recipe</h4>
          <p className="taste-line">{data.name}</p>
          <p className="small">
            We matched {data.coverage.matched} of {data.coverage.total} ingredients
            {data.used_grok ? " — a few were understood from the way you wrote them." : "."}
          </p>
          <details className="tech">
            <summary>Ingredient notes</summary>
            <ul className="lines">
              {data.lines.map((l) => (
                <li key={l.raw} className={`small line line-${l.status}`}>
                  <span className={`chip status-${l.status}`}>{l.status.replaceAll("_", " ")}</span> {l.raw}
                  {l.ingredient_id && ` → ${l.ingredient_id.replaceAll("_", " ")}`}
                  {l.grams != null && ` (${l.grams} g)`}
                  {l.note && <em className="muted"> {l.note}</em>}
                </li>
              ))}
            </ul>
          </details>
          <h4>Closest dishes</h4>
          <div className="neighbor-list">
            {data.neighbors.map((n, i) => {
              const d = dishOf(n.dish_id);
              if (!d) {
                return (
                  <p key={n.dish_id} className="small">
                    {i + 1}. {n.dish_id.replaceAll("_", " ")} · {closerThan(n.similarity_pct)}
                  </p>
                );
              }
              return (
                <DishCard
                  key={n.dish_id}
                  dish={d}
                  dims={space?.dims}
                  compact
                  onClick={() => {
                    useStore.getState().select(n.dish_id);
                    window.dispatchEvent(new Event("tastespace:show-map"));
                  }}
                />
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
