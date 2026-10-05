import json
from pathlib import Path

import pytest

from ideagate.agents import runner
from ideagate.config import load_config
from ideagate.db.repo import Repo

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).parent.parent


@pytest.fixture
def config(tmp_path):
    """The example config, with db and reports redirected into tmp_path."""
    import yaml

    raw = yaml.safe_load((ROOT / "ideagate.yaml.example").read_text())
    raw["paths"] = {"db": "test.db", "reports_dir": "reports"}
    path = tmp_path / "ideagate.yaml"
    path.write_text(yaml.safe_dump(raw))
    return load_config(path)


@pytest.fixture
def repo(config):
    return Repo(config.db_path)


@pytest.fixture
def fixture_backend():
    """Replays recorded raw results; fails the test if an unexpected extra call happens."""

    class Replay:
        def __init__(self):
            self.calls = []

        async def __call__(self, **kwargs):
            self.calls.append(kwargs)
            data = json.loads((FIXTURES / "normalizer_response.json").read_text())
            return runner.RawResult(**data)

    backend = Replay()
    original = runner.get_backend()
    runner.set_backend(backend)
    yield backend
    runner.set_backend(original)
