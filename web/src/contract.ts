// API types come ONLY from the generated contract (contracts/generated/api.d.ts, made by the
// integrator from the backend's pydantic models). Never hand-declare API shapes in web/.
import type { components } from "@contracts/generated/api";

type S = components["schemas"];

export type HealthResponse = S["HealthResponse"];
export type SpaceResponse = S["SpaceResponse"];
export type DishPoint = S["DishPoint"];
export type DimMeta = S["DimMeta"];
export type TwinsResponse = S["TwinsResponse"];
export type TwinResult = S["TwinResult"];
export type ShiftRequest = S["ShiftRequest"];
export type ShiftResponse = S["ShiftResponse"];
export type ExplainResponse = S["ExplainResponse"];
export type RecipeRequest = S["RecipeRequest"];
export type RecipeResponse = S["RecipeResponse"];
export type AskRequest = S["AskRequest"];
export type AskResponse = S["AskResponse"];
export type ChatMessage = S["ChatMessage"];
export type Contribution = S["Contribution"];
export type ErrorResponse = S["ErrorResponse"];
export type ErrorCode = S["ErrorBody"]["code"];

export type UiAction = AskResponse["ui_actions"][number];
export type DimId = DimMeta["id"];
export type Panel = NonNullable<S["AskContext"]["active_panel"]>;
export type Vec3 = DishPoint["xyz"];
export type Deltas = Partial<Record<DimId, number>>;
export type Course = DishPoint["course"];
export type DishFormat = DishPoint["format"];
export type ProvenanceSrc = Contribution["src"];
export type ToolTrace = AskResponse["tool_trace"][number];

export const asTriple = (v: Vec3): [number, number, number] => [v[0], v[1], v[2]];
