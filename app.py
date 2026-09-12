"""Vercel entrypoint. OWNER: integrator.

Builds the engine artifact into /tmp on a cold start (build/ is gitignored), then serves the FastAPI app.
Set XAI_API_KEY and GROK_MODEL in the Vercel project's environment variables to enable Ask.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "contracts" / "src")]
os.environ.setdefault("TASTESPACE_ROOT", str(ROOT))
os.environ.setdefault("TASTESPACE_BUILD_DIR", "/tmp/tastespace-build")

from fastapi.staticfiles import StaticFiles  # noqa: E402
from tastespace.build import main as build_main  # noqa: E402

if not (Path(os.environ["TASTESPACE_BUILD_DIR"]) / "tastespace.json").exists():
    build_main([])

from tastespace.api import app  # noqa: E402

# The web app, built in real mode (`cd web && VITE_API_MODE=real npx vite build --outDir ../static`), served
# from the same origin so its relative /api calls hit this app. Mounted last: /api routes win.
STATIC = ROOT / "static"
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="web")
