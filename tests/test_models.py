"""Tests for checklistfabrik.core.models."""

from checklistfabrik.core.models.checklist import Checklist
from checklistfabrik.core.models.page import Page, remove_last_divider
from checklistfabrik.core.models.task import Task


# --- Checklist ---


class TestChecklist:
    def test_len(self):
        pages = [Page("P1", [], None), Page("P2", [], None)]
        cl = Checklist("Test", pages, {})
        assert len(cl) == 2

    def test_to_dict_minimal(self):
        cl = Checklist("My CL", [], {})
        result = cl.to_dict()
        assert result["title"] == "My CL"
        assert result["pages"] == []
        assert "version" not in result

    def test_to_dict_with_version(self):
        cl = Checklist("My CL", [], {}, version="1.0.0")
        result = cl.to_dict()
        assert result["version"] == "1.0.0"

    def test_attributes(self):
        cl = Checklist("T", [], {}, description="Desc", report_path="rp", version="v1")
        assert cl.description == "Desc"
        assert cl.report_path == "rp"
        assert cl.version == "v1"


# --- remove_last_divider ---


class TestRemoveLastDivider:
    def test_removes_last_divider(self):
        html = '<p>A</p><div class="divider"></div><p>B</p><div class="divider"></div>'
        result = remove_last_divider(html)
        assert result.count("divider") == 1
        assert result == '<p>A</p><div class="divider"></div><p>B</p>'

    def test_no_divider(self):
        html = "<p>Hello</p>"
        assert remove_last_divider(html) == html


# --- Page ---


class TestPage:
    def test_to_dict_minimal(self):
        page = Page("Page Title", [], None)
        result = page.to_dict({})
        assert result["title"] == "Page Title"
        assert result["tasks"] == []
        assert "when" not in result

    def test_to_dict_with_when(self):
        page = Page("P", [], "x == 1")
        result = page.to_dict({})
        assert result["when"] == "x == 1"

    def test_eval_when_no_condition(self):
        page = Page("P", [], None)
        result, error = page.eval_when({})
        assert result == (True, None)
        assert error is None

    def test_eval_when_true(self):
        page = Page("P", [], "x == 1")
        result, error = page.eval_when({"x": 1})
        assert result is True
        assert error is None

    def test_eval_when_false(self):
        page = Page("P", [], "x == 99")
        result, error = page.eval_when({"x": 1})
        assert result is False
        assert error is None

    def test_eval_when_syntax_error(self):
        page = Page("P", [], "{%invalid%}")
        result, error = page.eval_when({})
        assert result is False
        assert error is not None
        assert "toast-error" in error

    def test_render_hidden_page(self, jinja_env, md):
        page = Page("Hidden", [], "show == true")
        html = page.render({"show": False}, jinja_env, md)
        assert "not applicable" in html

    def test_render_visible_page(self, jinja_env, md):
        page = Page("Visible", [], None)
        html = page.render({}, jinja_env, md)
        assert "Visible" in html


# --- Task ---


class TestTask:
    def test_to_dict_minimal(self):
        task = Task("linuxfabrik.clf.html", {"content": "hi"}, None, None)
        result = task.to_dict({})
        assert "linuxfabrik.clf.html" in result
        assert "fact_name" not in result
        assert "when" not in result

    def test_to_dict_with_fact_name_and_value(self):
        task = Task("linuxfabrik.clf.text_input", {"label": "Name"}, "user_name", None)
        result = task.to_dict({"user_name": "Alice"})
        assert result["fact_name"] == "user_name"
        assert result["value"] == "Alice"

    def test_to_dict_with_when(self):
        task = Task("linuxfabrik.clf.html", {"content": "x"}, None, "x == 1")
        result = task.to_dict({})
        assert result["when"] == "x == 1"

    def test_eval_when_no_condition(self):
        task = Task("m", {}, None, None)
        result, error = task.eval_when({})
        assert result == (True, None)
        assert error is None

    def test_eval_when_true(self):
        task = Task("m", {}, None, "x == 1")
        result, error = task.eval_when({"x": 1})
        assert result is True
        assert error is None

    def test_eval_when_false(self):
        task = Task("m", {}, None, "x == 99")
        result, error = task.eval_when({"x": 1})
        assert result is False
        assert error is None

    def test_render_hidden_task(self, jinja_env, md):
        task = Task("linuxfabrik.clf.html", {"content": "secret"}, None, "show == true")
        html = task.render({"show": False}, jinja_env, md)
        assert html == ""

    def test_render_html_module(self, jinja_env, md):
        task = Task("linuxfabrik.clf.html", {"content": "Hello"}, None, None)
        html = task.render({}, jinja_env, md)
        assert "Hello" in html

    def test_render_unknown_module(self, jinja_env, md):
        task = Task("nonexistent.module", {"content": "x"}, None, None)
        html = task.render({}, jinja_env, md)
        assert "toast-error" in html
        assert "Cannot find module" in html
