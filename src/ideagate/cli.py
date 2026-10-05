"""ideagate CLI: run, resume, show (list, rerun-stage, compare arrive in later milestones)."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ideagate.config import ConfigError, load_config
from ideagate.db.repo import Repo
from ideagate.pipeline.orchestrator import Orchestrator

app = typer.Typer(no_args_is_help=True, help="IdeaGate: validate an idea before you build it.")
console = Console()
ConfigOpt = typer.Option(None, "--config", "-c", help="Path to ideagate.yaml (default: ./ideagate.yaml or $IDEAGATE_CONFIG).")


def _setup(config_path: Optional[str]):
    try:
        cfg = load_config(config_path)
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2)
    return cfg, Repo(cfg.db_path)


@app.command()
def run(
    idea: str = typer.Argument(..., help="One-line product or app idea."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Optional extra context for the normalizer."),
    config: Optional[str] = ConfigOpt,
) -> None:
    """Run the pipeline on a new idea."""
    cfg, repo = _setup(config)
    orch = Orchestrator(cfg, repo)
    run_id = repo.create_run({"idea": idea, "notes": notes}).id
    console.print(f"Started run [bold]{run_id}[/bold]")
    try:
        orch.execute(run_id)
    except Exception as exc:
        console.print(f"[red]Run {run_id} failed:[/red] {exc}\nFix the cause, then: ideagate resume {run_id}")
        raise typer.Exit(1)
    _print_run(repo, run_id)


@app.command()
def resume(run_id: int, config: Optional[str] = ConfigOpt) -> None:
    """Continue a run from the last finished stage."""
    cfg, repo = _setup(config)
    if repo.get_run(run_id) is None:
        console.print(f"[red]Run {run_id} not found.[/red]")
        raise typer.Exit(1)
    try:
        Orchestrator(cfg, repo).resume(run_id)
    except Exception as exc:
        console.print(f"[red]Run {run_id} failed:[/red] {exc}")
        raise typer.Exit(1)
    _print_run(repo, run_id)


@app.command()
def show(run_id: int, config: Optional[str] = ConfigOpt) -> None:
    """Show a run: status, per-stage cost, and the stored outputs."""
    _, repo = _setup(config)
    if repo.get_run(run_id) is None:
        console.print(f"[red]Run {run_id} not found.[/red]")
        raise typer.Exit(1)
    _print_run(repo, run_id)


def _print_run(repo: Repo, run_id: int) -> None:
    run = repo.get_run(run_id)
    console.print(f"[bold]Run {run.id}[/bold]  status=[cyan]{run.status}[/cyan]  total=${run.total_usd:.4f}")
    if run.error:
        console.print(f"[red]error:[/red] {run.error}")
    table = Table("stage", "status", "model", "prompt", "usd", "secs")
    for sr in repo.stage_results(run_id):
        table.add_row(sr.stage, sr.status, sr.model or "-", sr.prompt_version or "-", f"${sr.usd:.4f}", f"{sr.duration_s:.1f}")
    console.print(table)
    done = repo.get_stage_result(run_id, "normalizer")
    if done and done.output_json:
        b = done.output_json
        console.print(f"\n[bold]{b['title']}[/bold]: {b['one_liner']}")
        console.print(f"Customer: {b['target_customer']}" + (f"  Buyer: {b['buyer']}" if b.get("buyer") else ""))
        console.print(f"Job to be done: {b['job_to_be_done']}\nWorkaround: {b['current_workaround']}")
        console.print("Riskiest assumptions:")
        for a in b["riskiest_assumptions"]:
            console.print(f"  - {a}")
        for d in b.get("possible_duplicates", []):
            console.print(f"[yellow]Possible duplicate of idea {d['idea_id']} ({d['similarity']:.0%}): {d['one_liner']}[/yellow]")


if __name__ == "__main__":
    app()
