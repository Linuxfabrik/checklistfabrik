"""Shared fixtures for ChecklistFabrik tests."""

import pathlib
import textwrap

import jinja2
import pytest
import ruamel.yaml

from checklistfabrik.core import markdown
from checklistfabrik.core.checklist_data_mapper import ChecklistDataMapper


TEMPLATES_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src"
    / "checklistfabrik"
    / "core"
    / "templates"
)


@pytest.fixture()
def jinja_env():
    """Jinja2 environment with project templates loaded."""
    return jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)))


@pytest.fixture()
def md():
    """Markdown renderer."""
    return markdown.create_markdown()


@pytest.fixture()
def data_mapper():
    """ChecklistDataMapper instance."""
    yaml = ruamel.yaml.YAML()
    return ChecklistDataMapper(yaml)


@pytest.fixture()
def sample_checklist_yaml(tmp_path):
    """Write a minimal checklist YAML to a temp file and return its path."""
    content = textwrap.dedent("""\
        title: Test Checklist
        pages:
          - title: Page One
            tasks:
              - linuxfabrik.clf.html:
                    content: Hello World
    """)
    file = tmp_path / "checklist.yml"
    file.write_text(content, encoding="utf-8")
    return file
