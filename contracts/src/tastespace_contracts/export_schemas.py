"""Write JSON Schemas for every data/ file type (editor autocompletion + drift check).

    uv run python -m tastespace_contracts.export_schemas contracts/schemas
"""

import json
import sys
from pathlib import Path

from .data_models import DATA_FILE_MODELS


def export(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in DATA_FILE_MODELS.items():
        path = out_dir / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "contracts/schemas")
    for p in export(target):
        print(f"wrote {p}")
