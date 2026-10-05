from ideagate.prompts import load_prompt


def test_normalizer_prompt_header_and_render():
    p = load_prompt("normalizer")
    assert (p.stage, p.output_schema) == ("normalizer", "IdeaBriefCore")
    assert p.version
    out = p.render(idea="X", notes_block="")
    assert "<untrusted_idea>\nX\n</untrusted_idea>" in out
    assert "{{" not in out
