"""FastAPI app. Every route declares its contract `response_model`; every failure returns the
contract ErrorResponse. Run: `make api` (uvicorn tastespace.api:app). OWNER: engine (P2)."""

from __future__ import annotations

import threading

from fastapi import FastAPI, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tastespace_contracts import CONTRACT_VERSION
from tastespace_contracts.api_models import (
    AskRequest,
    AskResponse,
    ExplainResponse,
    HealthResponse,
    RecipeRequest,
    RecipeResponse,
    ShiftRequest,
    ShiftResponse,
    SpaceResponse,
    TwinsResponse,
)
from tastespace_contracts.errors import ErrorBody, ErrorResponse
from tastespace_contracts.validate import Dataset, DataValidationError, load_dataset

from .config import Settings, get_settings
from .engine.explain import explain
from .engine.recipe import analyze_recipe
from .engine.shift import shift
from .engine.twins import find_twins
from .errors import TasteSpaceError
from .grok.agent import run_ask
from .grok.client import ChatFactory, xai_chat_factory
from .grok.ingredient_mapper import map_ingredients
from .state import EngineState

ERROR_RESPONSES: dict = {code: {"model": ErrorResponse} for code in (404, 422, 500, 502, 503)}


class Runtime:
    """Holds the build artifact (auto-reloads when `make build` rewrites it) and the dataset (recipes)."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._state: EngineState | None = None
        self._mtime: float | None = None
        self._ds: Dataset | None = None
        self._lock = threading.Lock()

    def state(self) -> EngineState:
        path = self.settings.artifact_path
        if not path.exists():
            raise TasteSpaceError("not_ready", "no build found - run `make build`")
        mtime = path.stat().st_mtime
        with self._lock:
            if self._state is None or mtime != self._mtime:
                try:
                    self._state = EngineState.load(path)
                except Exception as exc:
                    raise TasteSpaceError("not_ready", f"could not load build artifact: {exc}") from exc
                self._mtime, self._ds = mtime, None
            return self._state

    def dataset(self) -> Dataset:
        with self._lock:
            if self._ds is None:
                try:
                    self._ds = load_dataset(self.settings.data_dir, self.settings.data_tier)
                except DataValidationError as exc:
                    raise TasteSpaceError("not_ready", "data/ is invalid - run `make check-data`",
                                          {"errors": exc.errors[:20]}) from exc
            return self._ds


def _error(code: str, message: str, status: int, details: dict | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))  # type: ignore[arg-type]
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


def create_app(runtime: Runtime | None = None, chat_factory: ChatFactory | None = None) -> FastAPI:
    rt = runtime or Runtime()
    app = FastAPI(title="TasteSpace API", version=CONTRACT_VERSION, responses=ERROR_RESPONSES)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(TasteSpaceError)
    async def _ts_error(_: Request, exc: TasteSpaceError) -> JSONResponse:
        return _error(exc.code, exc.message, exc.status, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error("validation_error", "request did not match the contract", 422,
                      {"errors": jsonable_encoder(exc.errors())})

    @app.exception_handler(Exception)
    async def _internal(_: Request, exc: Exception) -> JSONResponse:
        return _error("internal", f"{type(exc).__name__}: {exc}", 500)

    def grok() -> ChatFactory:
        return chat_factory or xai_chat_factory(rt.settings)

    @app.get("/api/health", response_model=HealthResponse, operation_id="getHealth")
    def health() -> HealthResponse:
        build_id, build_ready, data_ready = None, False, False
        try:
            build_id, build_ready = rt.state().build_id, True
        except TasteSpaceError:
            pass
        try:
            rt.dataset()
            data_ready = True
        except TasteSpaceError:
            pass
        return HealthResponse(build_ready=build_ready, data_ready=data_ready,
                              grok_configured=chat_factory is not None or rt.settings.grok_configured,
                              contract_version=CONTRACT_VERSION, build_id=build_id)

    @app.get("/api/space", response_model=SpaceResponse, operation_id="getSpace")
    def get_space() -> SpaceResponse:
        return rt.state().space_response()

    @app.get("/api/twins", response_model=TwinsResponse, operation_id="getTwins")
    def get_twins(dish: str = Query(..., description="dish id"), k: int = Query(3, ge=1, le=10)) -> TwinsResponse:
        return find_twins(rt.state(), dish, k)

    @app.post("/api/shift", response_model=ShiftResponse, operation_id="postShift")
    def post_shift(req: ShiftRequest) -> ShiftResponse:
        return shift(rt.state(), req)

    @app.get("/api/explain", response_model=ExplainResponse, operation_id="getExplain")
    def get_explain(a: str = Query(...), b: str = Query(...)) -> ExplainResponse:
        return explain(rt.state(), a, b)

    @app.post("/api/recipe", response_model=RecipeResponse, operation_id="postRecipe")
    def post_recipe(req: RecipeRequest) -> RecipeResponse:
        state, ds = rt.state(), rt.dataset()
        try:
            factory = grok()
            mapper = lambda names: map_ingredients(names, ds.ingredients, factory)  # noqa: E731
        except TasteSpaceError:
            mapper = None  # Grok is optional for recipes: unmatched lines are simply reported
        return analyze_recipe(state, ds, req, mapper)

    @app.post("/api/ask", response_model=AskResponse, operation_id="postAsk")
    def post_ask(req: AskRequest) -> AskResponse:
        return run_ask(rt.state(), req, grok())

    return app


app = create_app()
