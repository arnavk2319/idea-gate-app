from typer.testing import CliRunner

from ideagate.cli import app
from tests.conftest import ROOT  # noqa: F401


def test_run_resume_show_end_to_end(config, tmp_path, fixture_backend):
    cfg_path = str(tmp_path / "ideagate.yaml")
    r = CliRunner()

    out = r.invoke(app, ["run", "Vue 2 migration audit", "-c", cfg_path])
    assert out.exit_code == 0, out.output
    assert "Vue 2 Migration Readiness Audit" in out.output

    out = r.invoke(app, ["resume", "1", "-c", cfg_path])
    assert out.exit_code == 0
    assert len(fixture_backend.calls) == 1  # resume did not redo Stage 0

    out = r.invoke(app, ["show", "1", "-c", cfg_path])
    assert out.exit_code == 0 and "$0.0123" in out.output


def test_missing_config_exits_cleanly(tmp_path):
    out = CliRunner().invoke(app, ["show", "1", "-c", str(tmp_path / "missing.yaml")])
    assert out.exit_code == 2
