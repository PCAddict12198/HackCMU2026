import type {
  AskRequest,
  AskResponse,
  ErrorCode,
  ExplainResponse,
  HealthResponse,
  RecipeRequest,
  RecipeResponse,
  ShiftRequest,
  ShiftResponse,
  SpaceResponse,
  TwinsResponse,
} from "../contract";

export class ApiError extends Error {
  code: ErrorCode | "network";
  status: number;
  details?: unknown;

  constructor(code: ErrorCode | "network", message: string, status = 0, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/** One interface, two implementations: mock (contract fixtures) and real (FastAPI). */
export interface TasteSpaceApi {
  health(): Promise<HealthResponse>;
  space(): Promise<SpaceResponse>;
  twins(dishId: string, k?: number): Promise<TwinsResponse>;
  shift(req: ShiftRequest): Promise<ShiftResponse>;
  explain(a: string, b: string): Promise<ExplainResponse>;
  recipe(req: RecipeRequest): Promise<RecipeResponse>;
  ask(req: AskRequest): Promise<AskResponse>;
}

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return `${e.code}: ${e.message}`;
  return e instanceof Error ? e.message : String(e);
}
