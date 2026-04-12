"""Tests for ChecklistFabrik task modules."""

import jinja2

from checklistfabrik.core.markdown import create_markdown
from checklistfabrik.modules.linuxfabrik.clf import (
    checkbox_input,
    html,
    markdown,
    radio_input,
    select_input,
    text_input,
)

from .conftest import TEMPLATES_DIR


def _make_kwargs(**extra):
    """Build kwargs dict as modules expect it."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(
            enabled_extensions=("html", "htm", "html.j2", "htm.j2"),
        ),
    )
    md = create_markdown()
    base = {
        "clf_jinja_env": env,
        "clf_markdown": md,
    }
    base.update(extra)
    return base


# --- html module ---


class TestHtmlModule:
    def test_basic_render(self):
        result = html.main(**_make_kwargs(content="Hello <b>World</b>"))
        assert "Hello <b>World</b>" in result["html"]
        assert "clf-content-block" in result["html"]

    def test_jinja_rendering(self):
        result = html.main(**_make_kwargs(content="Host: {{ host }}", host="server01"))
        assert "Host: server01" in result["html"]


# --- markdown module ---


class TestMarkdownModule:
    def test_basic_render(self):
        result = markdown.main(**_make_kwargs(content="**bold**"))
        assert "<strong>bold</strong>" in result["html"]
        assert "form-label" in result["html"]

    def test_jinja_in_markdown(self):
        result = markdown.main(**_make_kwargs(content="Hello {{ name }}", name="World"))
        assert "Hello World" in result["html"]


# --- text_input module ---


class TestTextInputModule:
    def test_basic_render(self):
        result = text_input.main(
            **_make_kwargs(
                fact_name="my_input",
                label="Enter value",
            )
        )
        assert 'name="my_input"' in result["html"]
        assert "Enter value" in result["html"]
        assert result["fact_name"] == "my_input"

    def test_required(self):
        result = text_input.main(
            **_make_kwargs(
                fact_name="req_input",
                label="Required",
                required=True,
            )
        )
        assert "required" in result["html"]

    def test_with_existing_value(self):
        result = text_input.main(
            **_make_kwargs(
                fact_name="prefilled",
                label="Test",
                prefilled="existing_value",
            )
        )
        assert result["fact_name"] == "prefilled"

    def test_auto_fact_name(self):
        result = text_input.main(
            **_make_kwargs(
                auto_fact_name="auto_abc123",
                label="Auto",
            )
        )
        assert result["fact_name"] == "auto_abc123"
        assert 'name="auto_abc123"' in result["html"]


# --- checkbox_input module ---


class TestCheckboxInputModule:
    def test_single_checkbox(self):
        result = checkbox_input.main(
            **_make_kwargs(
                fact_name="accept",
                label="Accept terms",
            )
        )
        assert 'name="accept"' in result["html"]
        assert 'type="checkbox"' in result["html"]
        assert result["fact_name"] == "accept"

    def test_multi_checkbox(self):
        result = checkbox_input.main(
            **_make_kwargs(
                fact_name="choices",
                label="Pick some",
                values=[
                    {"label": "A", "value": "a"},
                    {"label": "B", "value": "b"},
                ],
            )
        )
        assert 'name="choices[]"' in result["html"]
        assert result["fact_name"] == "choices"
        assert result["task_context_update"] is not None

    def test_required_single(self):
        result = checkbox_input.main(
            **_make_kwargs(
                fact_name="req",
                label="Required",
                required=True,
            )
        )
        assert "required" in result["html"]


# --- radio_input module ---


class TestRadioInputModule:
    def test_basic_render(self):
        result = radio_input.main(
            **_make_kwargs(
                fact_name="choice",
                label="Pick one",
                values=[
                    {"label": "Option A", "value": "a"},
                    {"label": "Option B", "value": "b"},
                ],
            )
        )
        assert 'type="radio"' in result["html"]
        assert 'name="choice"' in result["html"]
        assert "Option A" in result["html"]
        assert result["fact_name"] == "choice"

    def test_preselected(self):
        result = radio_input.main(
            **_make_kwargs(
                fact_name="color",
                label="Color",
                values=[
                    {"label": "Red", "value": "red"},
                    {"label": "Blue", "value": "blue"},
                ],
                color="red",
            )
        )
        assert "checked" in result["html"]

    def test_task_context_update(self):
        result = radio_input.main(
            **_make_kwargs(
                fact_name="x",
                label="X",
                values=[{"value": "v1"}],
            )
        )
        assert "task_context_update" in result
        assert len(result["task_context_update"]["values"]) == 1


# --- select_input module ---


class TestSelectInputModule:
    def test_single_select(self):
        result = select_input.main(
            **_make_kwargs(
                fact_name="country",
                label="Country",
                values=["CH", "DE", "AT"],
            )
        )
        assert "<select" in result["html"]
        assert 'name="country"' in result["html"]
        assert "Please select" in result["html"]
        assert result["fact_name"] == "country"

    def test_multi_select(self):
        result = select_input.main(
            **_make_kwargs(
                fact_name="langs",
                label="Languages",
                values=["Python", "Go"],
                multiple=True,
            )
        )
        assert 'name="langs[]"' in result["html"]
        assert "multiple" in result["html"]

    def test_preselected_single(self):
        result = select_input.main(
            **_make_kwargs(
                fact_name="os",
                label="OS",
                values=["Linux", "Windows"],
                os="Linux",
            )
        )
        assert "selected" in result["html"]

    def test_required(self):
        result = select_input.main(
            **_make_kwargs(
                fact_name="req",
                label="Required",
                values=["A", "B"],
                required=True,
            )
        )
        assert "required" in result["html"]
