// Canonical fixtures from contracts/fixtures/api (integrator-owned, validated against the pydantic
// models in CI). TS widens JSON string literals, hence the casts; the Python test is the real check.
import ask from "@contracts/fixtures/api/ask.json";
import errors from "@contracts/fixtures/api/errors.json";
import explain from "@contracts/fixtures/api/explain.json";
import health from "@contracts/fixtures/api/health.json";
import recipe from "@contracts/fixtures/api/recipe.json";
import shift from "@contracts/fixtures/api/shift.json";
import space from "@contracts/fixtures/api/space.json";
import spaceLarge from "@contracts/fixtures/api/space_large.json";
import twins from "@contracts/fixtures/api/twins.json";
import type {
  AskResponse,
  ErrorCode,
  ErrorResponse,
  ExplainResponse,
  HealthResponse,
  RecipeResponse,
  ShiftResponse,
  SpaceResponse,
  TwinsResponse,
} from "../contract";

export const fixtures = {
  health: health as unknown as HealthResponse,
  space: space as unknown as SpaceResponse,
  spaceLarge: spaceLarge as unknown as SpaceResponse,
  twins: twins as unknown as TwinsResponse,
  shift: shift as unknown as ShiftResponse,
  explain: explain as unknown as ExplainResponse,
  recipe: recipe as unknown as RecipeResponse,
  ask: ask as unknown as AskResponse,
  errors: errors as unknown as Record<ErrorCode, ErrorResponse>,
};
