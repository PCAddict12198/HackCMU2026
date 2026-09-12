"""Write the OpenAPI contract generated from the pydantic models (integrator runs `make contracts`).

    uv run python -m tastespace.export_openapi contracts/openapi.json
"""

import json
import sys
from pathlib import Path

from .api import create_app


def export(path: Path) -> None:
    spec = create_app().openapi()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "contracts/openapi.json")
    export(target)
    print(f"wrote {target}")
