// Recipe paste (baseline): POST /api/recipe, show match coverage honestly (matched / fuzzy / grok_mapped).
// P3 TODO: place the recipe as a new star in the galaxy (response.xyz), nicer line table.
import { useState } from "react";
import { api, errorMessage } from "../../api/client";
import type { RecipeResponse } from "../../contract";
import { useStore } from "../../state/store";

const SAMPLE = "200 g spaghetti\n100 g guanciale\n2 eggs\n50 g pecorino\n1 tsp black pepper";

export function RecipePanel() {
  const space = useStore((s) => s.space);
  const [text, setText] = useState(SAMPLE);
  const [data, setData] = useState<RecipeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setData(await api.recipe({ text }));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  const name = (id: string) => space?.dishes.find((d) => d.id === id)?.name ?? id;
  return (
    <div>
      <h3>Where does my recipe live?</h3>
      <textarea rows={7} value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={run} disabled={busy}>
        {busy ? "Placing..." : "Place recipe"}
      </button>
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          <p className="small">
            matched {data.coverage.matched}/{data.coverage.total} lines{data.used_grok && " (some mapped by Grok)"}
          </p>
          <ul>
            {data.lines.map((l) => (
              <li key={l.raw} className="small">
                <span className="chip">{l.status}</span> {l.raw} {l.ingredient_id && `-> ${l.ingredient_id}`}
                {l.grams != null && ` (${l.grams} g)`} {l.note && <em className="muted">{l.note}</em>}
              </li>
            ))}
          </ul>
          <p className="small">Nearest dishes: {data.neighbors.map((n) => name(n.dish_id)).join(", ")}</p>
        </>
      )}
    </div>
  );
}
