import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Course, DishFormat, RecipeResponse } from "../../contract";
import { closerThan } from "../shared/copy";
import { useStore } from "../../state/store";
import { ErrorState, Loading } from "../shared/Status";

const SAMPLE = "200 g spaghetti\n100 g guanciale\n2 eggs\n50 g pecorino\n1 tsp black pepper";
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
  const setExplainPair = useStore((s) => s.setExplainPair);
  const selectedId = useStore((s) => s.selectedId);
  const placeRecipeTick = useStore((s) => s.placeRecipeTick);
  const [text, setText] = useState(SAMPLE);
  const [course, setCourse] = useState<Course | "">("");
  const [format, setFormat] = useState<DishFormat | "">("");
  const [data, setData] = useState<RecipeResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.recipe({
        text,
        course: course || null,
        format: format || null,
      });
      setData(res);
      setRecipeStar(res);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (placeRecipeTick > 0) void run();
    // demo key 5 / first open
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [placeRecipeTick]);
  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  return (
    <div>
      <h3>Where does my recipe live?</h3>
      <textarea rows={7} value={text} onChange={(e) => setText(e.target.value)} />
      <div className="row">
        <select value={course} onChange={(e) => setCourse(e.target.value as Course | "")}>
          <option value="">any course</option>
          <option value="savory">savory</option>
          <option value="dessert">dessert</option>
        </select>
        <select value={format} onChange={(e) => setFormat(e.target.value as DishFormat | "")}>
          <option value="">any format</option>
          {FORMATS.map((f) => (
            <option key={f} value={f}>
              {f.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>
      <button type="button" onClick={run} disabled={busy}>
        {busy ? "Placing..." : "Place recipe"}
      </button>
      {error != null && <ErrorState error={error} onRetry={() => void run()} />}
      {busy && <Loading label="Placing recipe in the galaxy..." />}
      {data && (
        <>
          <p className="small">
            matched {data.coverage.matched}/{data.coverage.total} lines
            {data.used_grok && " (some mapped by Grok)"}
          </p>
          <ul className="lines">
            {data.lines.map((l) => (
              <li key={l.raw} className={`small line line-${l.status}`}>
                <span className={`chip status-${l.status}`}>{l.status}</span> {l.raw}
                {l.ingredient_id && ` → ${l.ingredient_id}`}
                {l.grams != null && ` (${l.grams} g)`}
                {l.status === "grok_mapped" && (
                  <em className="muted"> Grok chose this id from our ingredient list</em>
                )}
                {l.note && <em className="muted"> {l.note}</em>}
              </li>
            ))}
          </ul>
          <p className="small">
            Nearest dishes:{" "}
            {data.neighbors.map((n) => (
              <button
                key={n.dish_id}
                type="button"
                className="linkish"
                title={closerThan(n.similarity_pct)}
                onClick={() => {
                  if (selectedId) setExplainPair(selectedId, n.dish_id);
                  else setPanel("twins");
                }}
              >
                {name(n.dish_id)}
              </button>
            ))}
          </p>
        </>
      )}
    </div>
  );
}
