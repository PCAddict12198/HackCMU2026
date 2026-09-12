import type { ErrorResponse } from "../contract";
import { ApiError, type TasteSpaceApi } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  } catch (e) {
    throw new ApiError("network", `API unreachable (${String(e)}). Is \`make api\` running?`);
  }
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err = (body as ErrorResponse | null)?.error;
    throw new ApiError(err?.code ?? "internal", err?.message ?? res.statusText, res.status, err?.details);
  }
  return body as T;
}

const post = <T>(path: string, data: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(data) });

export const realApi: TasteSpaceApi = {
  health: () => request("/health"),
  space: () => request("/space"),
  twins: (dishId, k = 3) => request(`/twins?${new URLSearchParams({ dish: dishId, k: String(k) })}`),
  shift: (req) => post("/shift", req),
  explain: (a, b) => request(`/explain?${new URLSearchParams({ a, b })}`),
  recipe: (req) => post("/recipe", req),
  ask: (req) => post("/ask", req),
};
