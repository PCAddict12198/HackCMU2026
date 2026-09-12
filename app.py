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

from tastespace.build import main as build_main  # noqa: E402

if not (Path(os.environ["TASTESPACE_BUILD_DIR"]) / "tastespace.json").exists():
    build_main([])

from tastespace.api import app  # noqa: E402,F401
