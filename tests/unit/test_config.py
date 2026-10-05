import pytest
import yaml

from ideagate.config import ConfigError, load_config
from tests.conftest import ROOT


def _write(tmp_path, mutate):
    raw = yaml.safe_load((ROOT / "ideagate.yaml.example").read_text())
    mutate(raw)
    p = tmp_path / "ideagate.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p


def test_example_config_loads(config):
    assert config.budgets.run_usd_max == 3.0
    assert config.rubric.weights["proof_of_spending"] == 2.0


def test_placeholder_model_rejected(tmp_path):
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, lambda r: r["models"].update(strong="<set from current Anthropic model list>")))


def test_missing_rubric_column_rejected(tmp_path):
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, lambda r: r["rubric"]["weights"].pop("moat")))


def test_missing_file_has_helpful_message(tmp_path):
    with pytest.raises(ConfigError, match="ideagate.yaml.example"):
        load_config(tmp_path / "nope.yaml")
