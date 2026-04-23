# /// script
# dependencies = [
#     "marimo",
#     "tyro==0.9.5",
#     "python-dotenv==1.2.1",
#     "rich==14.3.2",
#     "wigglystuff==0.2.30",
#     "torch==2.11.0",
#     "mlflow==2.21.0",
#     "mlflow-widgets==0.4.0",
# ]
# requires-python = ">=3.11"
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="columns")


@app.cell(column=0, hide_code=True)
def _(mo):
    mo.md(r"""
    ## Notebook Description

    Dual-mode marimo notebook: edit interactively or run as a CLI script via
    `uv run starting-point.py --epochs 50 --batch-size 64`. Tracks training
    runs to MLflow and (in edit mode) shows a live loss chart via
    `mlflow-widgets`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Environment Keys""")
    return


@app.cell
def _():
    import os
    import marimo as mo
    from dotenv import load_dotenv

    load_dotenv(".env")
    return mo, os


@app.cell
def _(env_config, is_script_mode):
    env_config if not is_script_mode else None
    return


@app.cell
def _(ModelParams, mo, mlflow, os):
    from wigglystuff import EnvConfig
    import sys
    import tyro

    is_script_mode = mo.app_meta().mode == "script"

    env_config = mo.ui.anywidget(
        EnvConfig({
            # Validator: try listing experiments. Returns truthy on success.
            "MLFLOW_TRACKING_URI": lambda u: bool(
                mlflow.MlflowClient(tracking_uri=u).search_experiments(max_results=1)
                or True
            ),
            # Token is optional and presence-only (no cheap validation endpoint).
            "MLFLOW_TRACKING_TOKEN": lambda _: True,
        })
    )

    if is_script_mode:
        # Tyro auto-generates --help and parses CLI args into ModelParams.
        # Note: we call tyro here (not in the params cell) so script-mode dispatch
        # happens before any heavy imports below.
        params_from_cli = tyro.cli(ModelParams)
    else:
        params_from_cli = None

    return env_config, is_script_mode, params_from_cli


@app.cell
def _():
    import mlflow

    return (mlflow,)


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""## Training Parameters""")
    return


@app.cell
def _(params_form):
    params_form
    return


@app.cell
def _():
    import hashlib
    import json
    from dataclasses import dataclass, asdict, field

    @dataclass
    class ModelParams:
        """Model training parameters."""

        epochs: int = 25
        """Number of training epochs."""
        batch_size: int = 32
        """Training batch size."""
        learning_rate: float = 1e-4
        """Learning rate for AdamW."""
        mlflow_experiment: str = "batch-sizes"
        """MLflow experiment name (empty string disables logging)."""
        mlflow_run_name: str = ""
        """Optional explicit run name; auto-derived from params if empty."""

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

    return ModelParams, asdict


@app.cell
def _(mo):
    params_form = (
        mo.md("""
    ## Model parameters

    {epochs}
    {batch_size}
    {learning_rate}
    {mlflow_experiment}
    """)
        .batch(
            epochs=mo.ui.slider(10, 50, value=25, step=1, label="epochs"),
            batch_size=mo.ui.slider(8, 512, value=32, step=8, label="batch size"),
            learning_rate=mo.ui.slider(
                1e-5, 5e-4, value=1e-4, step=1e-5, label="learning rate"
            ),
            mlflow_experiment=mo.ui.text(
                value="batch-sizes", label="mlflow experiment"
            ),
        )
        .form()
    )
    return (params_form,)


@app.cell
def _(ModelParams, is_script_mode, mo, params_form, params_from_cli):
    mo.stop(
        not is_script_mode and params_form.value is None,
        mo.md("*Submit the form to start training.*"),
    )

    if is_script_mode:
        params = params_from_cli
    else:
        params = ModelParams(**params_form.value)

    return (params,)


@app.cell(hide_code=True)
def _(mo, params):
    mo.md(f"**Active params:** `{params}`")
    return


@app.cell
def _():
    import torch
    import torch.nn as nn

    return nn, torch


@app.cell(column=2, hide_code=True)
def _(mo):
    mo.md(r"""## Data Setup""")
    return


@app.cell
def _(params, torch):
    X = torch.randn(1000, 10)
    w_true = torch.randn(10, 1)
    y = X @ w_true + 0.1 * torch.randn(1000, 1)

    dataset = torch.utils.data.TensorDataset(X, y)
    train_loader = torch.utils.data.DataLoader(
        dataset, batch_size=params.batch_size, shuffle=True
    )
    return (train_loader,)


@app.cell(column=3, hide_code=True)
def _(mo):
    mo.md(r"""## Model Setup""")
    return


@app.cell
def _(nn):
    model = nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )

    model
    return (model,)


@app.cell(column=4, hide_code=True)
def _(mo):
    mo.md(r"""## Live MLflow Chart (UI mode only)""")
    return


@app.cell
def _(is_script_mode, mlflow, mo, os, params):
    # Live chart is UI-only; in script mode we skip rendering entirely.
    if not is_script_mode and params.mlflow_experiment:
        from mlflow_widgets import MlflowChart

        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
        client = mlflow.MlflowClient(tracking_uri=tracking_uri)
        try:
            exp = client.get_experiment_by_name(params.mlflow_experiment)
            experiment_id = exp.experiment_id if exp else None
        except Exception:
            experiment_id = None

        if experiment_id:
            live_chart = mo.ui.anywidget(
                MlflowChart(
                    tracking_uri=tracking_uri,
                    experiment_id=experiment_id,
                    metric_key="loss",
                )
            )
        else:
            live_chart = mo.md(
                "*MLflow experiment not yet created. Run training once to "
                "populate it, then re-run this cell.*"
            )
    else:
        live_chart = None
    live_chart
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Training Loop""")
    return


@app.cell
def _(asdict, mlflow, mo, model, nn, os, params, torch, train_loader):
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    if params.mlflow_experiment:
        mlflow.set_experiment(params.mlflow_experiment)
        run_ctx = mlflow.start_run(run_name=params.derived_run_name())
        # Log all params except the mlflow_* config fields.
        mlflow.log_params(
            {k: v for k, v in asdict(params).items() if not k.startswith("mlflow_")}
        )
    else:
        run_ctx = None

    optimizer = torch.optim.AdamW(model.parameters(), lr=params.learning_rate)
    loss_fn = nn.MSELoss()

    avg_loss = float("nan")
    with mo.status.progress_bar(total=params.epochs) as bar:
        for epoch in range(params.epochs):
            epoch_loss = 0.0
            for xb, yb in train_loader:
                pred = model(xb)
                loss = loss_fn(pred, yb)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg_loss = epoch_loss / len(train_loader)
            if run_ctx:
                mlflow.log_metric("loss", avg_loss, step=epoch)
            bar.update()

    if run_ctx:
        mlflow.end_run()

    mo.md(f"**Training complete.** Final loss: `{avg_loss:.6f}`")
    return


if __name__ == "__main__":
    app.run()
