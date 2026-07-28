"""Shared fixtures for ChecklistFabrik tests."""

import pathlib
import textwrap

import jinja2
import pytest
import ruamel.yaml

from checklistfabrik.core import export, markdown
from checklistfabrik.core.checklist_data_mapper import ChecklistDataMapper

TEMPLATES_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'src'
    / 'checklistfabrik'
    / 'core'
    / 'templates'
)


@pytest.fixture()
def jinja_env():
    """Jinja2 environment with project templates loaded."""
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(
            enabled_extensions=('html', 'htm', 'html.j2', 'htm.j2'),
        ),
    )


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
    file = tmp_path / 'checklist.yml'
    file.write_text(content, encoding='utf-8')
    return file


@pytest.fixture()
def sample_report_yaml(tmp_path):
    """Write a partially completed report covering every built-in task module."""
    content = textwrap.dedent("""\
        title: 'Server Maintenance {{ ticket }}'
        description: 'Monthly maintenance procedure.'
        version: '2026072801'

        pages:
          - title: 'Preparation'
            tasks:
              - linuxfabrik.clf.markdown:
                    content: |
                        ### Scope

                        Covers **all** servers in `dc-01`.

                        - Database nodes
                        - Web nodes

              - linuxfabrik.clf.text_input:
                    label: 'Ticket number'
                    required: true
                fact_name: 'ticket'
                value: 'INC-4711'

              - linuxfabrik.clf.radio_input:
                    label: 'Maintenance type'
                    values:
                      - label: 'Full **update**'
                        value: 'full'
                      - label: 'Security only'
                        value: 'security'
                fact_name: 'maint_type'
                value: 'full'

              - linuxfabrik.clf.checkbox_input:
                    label: 'Pre-flight checks'
                    values:
                      - label: 'Notify users'
                        value: 'notify'
                      - label: 'Create a backup'
                        value: 'backup'
                        required: true
                fact_name: 'preflight'
                value:
                  - 'notify'

          - title: 'Maintenance'
            tasks:
              - linuxfabrik.clf.textarea_input:
                    label: 'Command output'
                    monospace: true
                fact_name: 'output'
                value: |
                  first line
                  second line

              - linuxfabrik.clf.text_input:
                    label: 'Reboot duration'
                fact_name: 'reboot_duration'

              - linuxfabrik.clf.html:
                    content: '<p>Raw <b>HTML</b> for {{ ticket }}.</p>'

          - title: 'Security updates only'
            when: "maint_type == 'security'"
            tasks:
              - linuxfabrik.clf.text_input:
                    label: 'CVE identifier'
                fact_name: 'cve'
    """)
    file = tmp_path / 'report.yml'
    file.write_text(content, encoding='utf-8')
    return file


@pytest.fixture()
def sample_document(data_mapper, sample_report_yaml):
    """Build the neutral export document of the sample report."""
    checklist = data_mapper.load_checklist(sample_report_yaml)

    return export.build_document(checklist, source=sample_report_yaml.name)
