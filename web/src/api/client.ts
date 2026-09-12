// Pick the data source once: VITE_API_MODE=mock (default, fixtures) or real (FastAPI via the Vite proxy).
import { mockApi } from "./mock";
import { realApi } from "./real";
import type { TasteSpaceApi } from "./types";

export const API_MODE: "mock" | "real" = import.meta.env.VITE_API_MODE === "real" ? "real" : "mock";
export const api: TasteSpaceApi = API_MODE === "real" ? realApi : mockApi;
export { ApiError, errorMessage } from "./types";
