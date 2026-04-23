# /// script
# dependencies = [
#     "marimo",
#     "tyro==0.9.5",
#     "pydantic==2.12.5",
# ]
# requires-python = ">=3.11"
# ///
"""
Pydantic variant of the ModelParams cell from starting-point.py.

Use this when you need Pydantic features (validators, computed fields, JSON
schema, strict types) instead of stdlib dataclass. The rest of the notebook
in starting-point.py is unchanged — only the params cell differs.

Tyro v0.8+ supports `pydantic.BaseModel` directly: `tyro.cli(ModelParams)`
parses CLI flags into a validated Pydantic model. Field(description=...)
becomes the CLI --help text.
"""

from pydantic import BaseModel, Field, computed_field
import hashlib
import json
import tyro


class ModelParams(BaseModel):
    epochs: int = Field(default=25, description="Number of training epochs.")
    batch_size: int = Field(default=32, description="Training batch size.")
    learning_rate: float = Field(
        default=1e-4, description="Learning rate for AdamW."
    )
    mlflow_experiment: str = Field(
        default="batch-sizes",
        description="MLflow experiment name (empty disables logging).",
    )
    mlflow_run_name: str = Field(
        default="",
        description="Optional explicit run name; auto-derived if empty.",
    )

    @computed_field
    @property
    def derived_run_name(self) -> str:
        if self.mlflow_run_name:
            return self.mlflow_run_name
        parts = [
            f"e{self.epochs}",
            f"bs{self.batch_size}",
            f"lr{self.learning_rate:.0e}",
        ]
        params_dict = {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
        }
        h = hashlib.md5(
            json.dumps(params_dict, sort_keys=True).encode()
        ).hexdigest()[:6]
        return "-".join(parts) + f"-{h}"


if __name__ == "__main__":
    # Standalone smoke test: `uv run params-pydantic.py --help`
    params = tyro.cli(ModelParams)
    print(params)
    print("derived_run_name:", params.derived_run_name)
