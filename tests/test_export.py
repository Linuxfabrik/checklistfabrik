"""Tests for the static export of ChecklistFabrik reports."""

import logging
import pathlib
import textwrap

import jinja2
import pytest
import werkzeug.test

from checklistfabrik.core import dashboard_wsgi_app, export, templates
from checklistfabrik.core.cli.export import ExportCli
from checklistfabrik.core.export import blocks, markup
from checklistfabrik.core.export.renderers import asciidoc, html, markdown, pdf, rst

TEXT_FORMATS = ('asciidoc', 'html', 'markdown', 'rst')


def _export_kwargs(**extra):
    """Build the kwargs a task module receives while exporting."""
    env = jinja2.Environment(autoescape=False)
    base = {
        'clf_jinja_env': env,
        'clf_jinja_env_plain': env,
        'clf_markdown': lambda text: text,
    }
    base.update(extra)
    return base


# --- markup writers ---


class TestRstWriter:
    def test_inline_markup(self):
        writer = markup.RstWriter()
        assert writer.render('**bold** and *italic*') == '**bold** and *italic*'
        assert writer.render('`code`') == '``code``'
        assert (
            writer.render('[text](https://example.com)')
            == '`text <https://example.com>`_'
        )

    def test_escapes_literal_markup_characters(self):
        assert (
            markup.RstWriter().render('2 * 3 and a | pipe') == r'2 \* 3 and a \| pipe'
        )

    def test_headings_become_bold_paragraphs(self):
        # An arbitrary heading level inside a task would break the section hierarchy of
        # the surrounding document.
        assert markup.RstWriter().render('### Scope') == '**Scope**'

    def test_code_block_uses_the_docutils_directive(self):
        result = markup.RstWriter().render('```bash\nsystemctl stop nginx\n```')
        assert result == '.. code:: bash\n\n   systemctl stop nginx'

    def test_code_block_without_language(self):
        assert markup.RstWriter().render('```\nplain\n```') == '::\n\n   plain'

    def test_table_becomes_list_table(self):
        result = markup.RstWriter().render('| a | b |\n|---|---|\n| 1 | 2 |\n')
        assert result.startswith('.. list-table::\n   :header-rows: 1')
        assert '   * - a' in result
        assert '     - b' in result

    def test_quote_uses_a_directive(self):
        # A plain indented block would be swallowed by a preceding directive.
        assert markup.RstWriter().render('> quoted') == '.. pull-quote::\n\n   quoted'

    def test_nested_list_is_indented(self):
        result = markup.RstWriter().render('- outer\n  - inner\n')
        assert '- outer' in result
        assert '  - inner' in result


class TestMarkdownWriter:
    def test_inline_markup_round_trip(self):
        writer = markup.MarkdownWriter()
        assert writer.render('**bold** `code`') == '**bold** `code`'
        assert writer.render('~~gone~~') == '~~gone~~'

    def test_headings_are_shifted_below_the_page_heading(self):
        assert (
            markup.MarkdownWriter().render('# Top\n\n## Sub\n') == '### Top\n\n#### Sub'
        )

    def test_heading_shift_is_relative_to_the_topmost_heading(self):
        assert markup.MarkdownWriter().render('### Only') == '### Only'

    def test_heading_level_is_capped(self):
        result = markup.MarkdownWriter().render('# Top\n\n###### Deep\n')

        assert result == '### Top\n\n###### Deep'


class TestAsciiDocWriter:
    def test_inline_markup(self):
        writer = markup.AsciiDocWriter()
        assert writer.render('**bold**') == '*bold*'
        assert writer.render('`code`') == '`+code+`'
        assert (
            writer.render('[text](https://example.com)') == 'https://example.com[text]'
        )

    def test_nested_list_repeats_the_marker(self):
        # AsciiDoc reads an indented line as a literal block.
        result = markup.AsciiDocWriter().render('- outer\n  - inner\n')
        assert result == '* outer\n** inner'

    def test_code_block(self):
        result = markup.AsciiDocWriter().render('```bash\nls\n```')
        assert result == '[source,bash]\n----\nls\n----'


class TestTextWriter:
    def test_drops_markup(self):
        assert markup.TextWriter().render('**bold** and `code`') == 'bold and code'

    def test_keeps_html_text_content(self):
        assert markup.TextWriter().render('<p>Raw <b>HTML</b></p>') == 'Raw HTML'


# --- blocks ---


class TestBlocks:
    def test_values_of_normalises_to_a_list_of_strings(self):
        assert blocks.values_of(None) == []
        assert blocks.values_of('') == []
        assert blocks.values_of('value') == ['value']
        assert blocks.values_of(['a', '', None, 'b']) == ['a', 'b']
        assert blocks.values_of(7) == ['7']

    def test_plain_text_strips_markdown(self):
        assert blocks.plain_text('Full **update**') == 'Full update'


# --- neutral document ---


class TestDocument:
    def test_metadata(self, sample_document):
        assert sample_document['title'] == 'Server Maintenance INC-4711'
        assert sample_document['description'] == 'Monthly maintenance procedure.'
        assert sample_document['generator'].startswith('ChecklistFabrik v')
        assert sample_document['source'] == 'report.yml'
        assert sample_document['version'] == '2026072801'

    def test_metadata_can_be_switched_off(self, data_mapper, sample_report_yaml):
        checklist = data_mapper.load_checklist(sample_report_yaml)
        document = export.build_document(checklist, include_metadata=False)

        assert document['generator'] is None

    def test_page_titles_are_rendered_through_jinja(self, sample_document):
        assert [page['title'] for page in sample_document['pages']] == [
            'Preparation',
            'Maintenance',
            'Security updates only',
        ]

    def test_excluded_page_is_kept_but_flagged(self, sample_document):
        assert [page['applicable'] for page in sample_document['pages']] == [
            True,
            True,
            False,
        ]

    def test_progress_ignores_excluded_pages(self, sample_document):
        # ticket, maintenance type, two pre-flight items, command output, reboot duration.
        assert sample_document['stats'] == {
            'complete': False,
            'done': 4,
            'percent': 67,
            'total': 6,
        }

    def test_progress_of_a_completed_checklist(self):
        pages = [
            {
                'applicable': True,
                'tasks': [
                    {
                        'applicable': True,
                        'blocks': [blocks.field('Done', ['yes'])],
                    },
                ],
            },
        ]

        assert export.document.count_progress(pages) == {
            'complete': True,
            'done': 1,
            'percent': 100,
            'total': 1,
        }

    def test_blocks_of_a_field(self, sample_document):
        task = sample_document['pages'][0]['tasks'][1]

        assert task['blocks'] == [
            {
                'label': 'Ticket number',
                'monospace': False,
                'required': True,
                'type': 'field',
                'values': ['INC-4711'],
            },
        ]

    def test_unknown_module_yields_an_error_note(self, data_mapper, tmp_path):
        report = tmp_path / 'unknown.yml'
        report.write_text(
            'title: T\npages:\n  - title: P\n    tasks:\n      - does.not.exist: {}\n',
            encoding='utf-8',
        )
        document = export.build_document(data_mapper.load_checklist(report))
        block = document['pages'][0]['tasks'][0]['blocks'][0]

        assert block['type'] == 'note'
        assert block['level'] == 'error'
        assert 'does.not.exist' in block['content']


# --- task module export functions ---


class TestModuleExport:
    def test_text_input(self):
        from checklistfabrik.modules.linuxfabrik.clf import text_input

        result = text_input.export(
            **_export_kwargs(
                fact_name='host', host='server01', label='Host', required=True
            )
        )

        assert result['fact_name'] == 'host'
        assert result['blocks'] == [
            {
                'label': 'Host',
                'monospace': False,
                'required': True,
                'type': 'field',
                'values': ['server01'],
            },
        ]

    def test_textarea_input_keeps_the_monospace_flag(self):
        from checklistfabrik.modules.linuxfabrik.clf import textarea_input

        result = textarea_input.export(
            **_export_kwargs(
                fact_name='out', label='Output', monospace=True, out='a\nb'
            )
        )

        assert result['blocks'][0]['monospace'] is True
        assert result['blocks'][0]['values'] == ['a\nb']

    def test_select_input_multiple_values(self):
        from checklistfabrik.modules.linuxfabrik.clf import select_input

        result = select_input.export(
            **_export_kwargs(
                fact_name='langs', label='Languages', langs=['Python', 'Go']
            )
        )

        assert result['blocks'][0]['values'] == ['Python', 'Go']

    def test_radio_input_reports_the_selected_label(self):
        from checklistfabrik.modules.linuxfabrik.clf import radio_input

        result = radio_input.export(
            **_export_kwargs(
                fact_name='type',
                label='Type',
                type='full',
                values=[
                    {'label': 'Full **update**', 'value': 'full'},
                    {'label': 'Security only', 'value': 'security'},
                ],
            )
        )

        # The label is Markdown, the value is plain text.
        assert result['blocks'][0]['values'] == ['Full update']

    def test_radio_input_falls_back_to_the_raw_value(self):
        from checklistfabrik.modules.linuxfabrik.clf import radio_input

        result = radio_input.export(
            **_export_kwargs(
                fact_name='type',
                label='Type',
                type='removed',
                values=[{'label': 'Full', 'value': 'full'}],
            )
        )

        assert result['blocks'][0]['values'] == ['removed']

    def test_checkbox_input_group(self):
        from checklistfabrik.modules.linuxfabrik.clf import checkbox_input

        result = checkbox_input.export(
            **_export_kwargs(
                fact_name='checks',
                checks=['a'],
                label='Checks',
                values=[
                    {'label': 'First', 'value': 'a'},
                    {'label': 'Second', 'value': 'b', 'required': True},
                ],
            )
        )
        block = result['blocks'][0]

        assert block['type'] == 'checklist'
        assert block['label'] == 'Checks'
        assert block['items'] == [
            {'checked': True, 'label': 'First', 'required': False},
            {'checked': False, 'label': 'Second', 'required': True},
        ]

    def test_checkbox_input_single(self):
        from checklistfabrik.modules.linuxfabrik.clf import checkbox_input

        result = checkbox_input.export(
            **_export_kwargs(
                fact_name='accept', accept='on', label='Accept', required=True
            )
        )

        assert result['blocks'][0]['items'] == [
            {'checked': True, 'label': 'Accept', 'required': True},
        ]

    def test_markdown_and_html_keep_their_source(self):
        from checklistfabrik.modules.linuxfabrik.clf import html as html_module
        from checklistfabrik.modules.linuxfabrik.clf import markdown as markdown_module

        assert markdown_module.export(**_export_kwargs(content='# {{ x }}', x='Title'))[
            'blocks'
        ] == [
            {'content': '# Title', 'type': 'markdown'},
        ]
        assert html_module.export(**_export_kwargs(content='<b>{{ x }}</b>', x='raw'))[
            'blocks'
        ] == [
            {'content': '<b>raw</b>', 'type': 'html'},
        ]

    def test_run_template_reference(self, tmp_path):
        from checklistfabrik.modules.linuxfabrik.clf import run_template

        target = tmp_path / 'target.yml'
        target.write_text('title: Sub Checklist\ndescription: Runs later.\npages: []\n')

        result = run_template.export(
            **_export_kwargs(
                clf_task_workdir=tmp_path,
                fact_name='done',
                done='on',
                path='target.yml',
                required=True,
            )
        )

        assert result['blocks'] == [
            {
                'checked': True,
                'description': 'Runs later.',
                'label': 'Sub Checklist',
                'path': 'target.yml',
                'required': True,
                'type': 'reference',
            },
        ]

    def test_run_template_error_becomes_a_note(self, tmp_path):
        from checklistfabrik.modules.linuxfabrik.clf import run_template

        result = run_template.export(
            **_export_kwargs(
                clf_task_workdir=tmp_path, fact_name='done', path='missing.yml'
            )
        )

        assert result['blocks'][0]['type'] == 'note'
        assert result['blocks'][0]['level'] == 'error'


# --- renderers ---


class TestRstRenderer:
    def test_title_and_metadata(self, sample_document):
        result = rst.render(sample_document)

        assert result.startswith(
            '===========================\n'
            'Server Maintenance INC-4711\n'
            '===========================\n'
        )
        assert ':Source: ``report.yml``' in result
        assert ':Progress: 4 of 6 items completed (67%)' in result
        assert ':Version: 2026072801' in result

    def test_pages_are_sections(self, sample_document):
        assert 'Preparation\n===========' in rst.render(sample_document)

    def test_field(self, sample_document):
        assert 'Ticket number *(required)*\n   INC-4711' in rst.render(sample_document)

    def test_unanswered_field(self, sample_document):
        assert 'Reboot duration\n   *not answered*' in rst.render(sample_document)

    def test_multiline_value_becomes_a_literal_block(self, sample_document):
        assert '::\n\n      first line\n      second line' in rst.render(
            sample_document
        )

    def test_checklist_markers(self, sample_document):
        result = rst.render(sample_document)

        assert '- [x] Notify users' in result
        assert '- [ ] Create a backup *(required)*' in result

    def test_excluded_page_gets_a_note(self, sample_document):
        result = rst.render(sample_document)

        assert '.. note::\n\n   This page was marked as not applicable' in result

    def test_raw_html_becomes_a_raw_directive(self, sample_document):
        assert '.. raw:: html\n\n   <p>Raw <b>HTML</b> for INC-4711.</p>' in rst.render(
            sample_document
        )


class TestMarkdownRenderer:
    def test_title_and_metadata(self, sample_document):
        result = markdown.render(sample_document)

        assert result.startswith('# Server Maintenance INC-4711')
        assert '- **Source:** `report.yml`' in result

    def test_required_marker_sits_outside_the_bold_label(self, sample_document):
        # `**label *(required)***` would be an ambiguous run of emphasis markers.
        assert '**Ticket number** *(required)*' in markdown.render(sample_document)

    def test_task_list_syntax(self, sample_document):
        assert '- [x] Notify users' in markdown.render(sample_document)

    def test_monospace_value_becomes_a_fenced_block(self, sample_document):
        assert '```\nfirst line\nsecond line\n```' in markdown.render(sample_document)


class TestAsciiDocRenderer:
    def test_title_and_metadata(self, sample_document):
        result = asciidoc.render(sample_document)

        assert result.startswith('= Server Maintenance INC-4711')
        assert '[horizontal]' in result
        assert 'Source:: `+report.yml+`' in result

    def test_pages_are_sections(self, sample_document):
        assert '== Preparation' in asciidoc.render(sample_document)

    def test_checklist_syntax(self, sample_document):
        assert '* [x] Notify users' in asciidoc.render(sample_document)

    def test_excluded_page_gets_an_admonition(self, sample_document):
        assert (
            '[NOTE]\n====\nThis page was marked as not applicable'
            in asciidoc.render(sample_document)
        )


class TestHtmlRenderer:
    def test_is_self_contained(self, sample_document):
        result = html.render(sample_document)

        assert result.startswith('<!DOCTYPE html>')
        assert '<style>' in result
        # No external resource may be referenced.
        assert 'src=' not in result
        assert '<link' not in result

    def test_title_and_metadata(self, sample_document):
        result = html.render(sample_document)

        assert '<title>Server Maintenance INC-4711</title>' in result
        assert '<dt>Source</dt><dd><code>report.yml</code></dd>' in result

    def test_raw_html_is_kept(self, sample_document):
        assert '<p>Raw <b>HTML</b> for INC-4711.</p>' in html.render(sample_document)

    def test_values_are_escaped(self, data_mapper, tmp_path):
        report = tmp_path / 'escape.yml'
        report.write_text(
            'title: T\n'
            'pages:\n'
            '  - title: P\n'
            '    tasks:\n'
            '      - linuxfabrik.clf.text_input:\n'
            "            label: 'Value'\n"
            "        fact_name: 'v'\n"
            "        value: '<script>alert(1)</script>'\n",
            encoding='utf-8',
        )
        result = html.render(export.build_document(data_mapper.load_checklist(report)))

        assert '<script>alert(1)</script>' not in result
        assert '&lt;script&gt;' in result


class TestPdfRenderer:
    def test_renders_a_pdf(self, sample_document):
        pytest.importorskip(
            'fpdf', reason='PDF export needs the optional fpdf2 package'
        )

        data = export.render(sample_document, 'pdf')

        assert data.startswith(b'%PDF-')

    def test_renders_structured_markdown(self, data_mapper, tmp_path):
        pytest.importorskip(
            'fpdf', reason='PDF export needs the optional fpdf2 package'
        )

        report = tmp_path / 'structure.yml'
        report.write_text(
            textwrap.dedent("""\
                title: Structure
                pages:
                  - title: Page
                    tasks:
                      - linuxfabrik.clf.markdown:
                            content: |
                                # Heading

                                1. First
                                2. Second
                                   - Nested

                                | a | b |
                                |---|---|
                                | 1 | 2 |

                                > Quoted

                                ---

                                ```bash
                                systemctl stop nginx
                                ```
            """),
            encoding='utf-8',
        )
        document = export.build_document(data_mapper.load_checklist(report))

        assert export.render(document, 'pdf').startswith(b'%PDF-')

    def test_escapes_the_markers_of_fpdf(self):
        # `--verbose` would otherwise underline the rest of the paragraph.
        rendered = pdf.InlineWriter().render('Run `dnf --refresh` with --verbose')

        assert rendered == r'Run dnf \--refresh with \--verbose'

    def test_keeps_emphasis_in_content(self):
        rendered = pdf.InlineWriter().render('**bold**, *italic*, ~~gone~~')

        assert rendered == '**bold**, __italic__, ~~gone~~'

    def test_label_markup_is_dropped(self):
        # A label is written in a bold font, so its emphasis cannot be handed to fpdf2.
        lead, _rest = markup.split_lead_paragraph('Full **update**')

        assert pdf.plain_inline(lead['children']) == 'Full update'

    def test_missing_dependency_raises_an_export_error(
        self, monkeypatch, sample_document
    ):
        from checklistfabrik.core.export.renderers import pdf

        def no_fpdf():
            raise export.ExportError('PDF export requires the "fpdf2" package.')

        monkeypatch.setattr(pdf, '_import_fpdf', no_fpdf)

        with pytest.raises(export.ExportError, match='fpdf2'):
            pdf.render(sample_document)


# --- public export API ---


class TestExportApi:
    @pytest.mark.parametrize(
        ('path', 'expected'),
        [
            ('report.adoc', 'asciidoc'),
            ('report.asciidoc', 'asciidoc'),
            ('report.HTML', 'html'),
            ('report.md', 'markdown'),
            ('report.pdf', 'pdf'),
            ('report.rst', 'rst'),
            ('report.yml', None),
            ('report', None),
        ],
    )
    def test_format_from_suffix(self, path, expected):
        assert export.format_from_suffix(path) == expected

    def test_output_path_replaces_the_extension(self):
        assert export.output_path('reports/run.yml', 'rst') == pathlib.Path(
            'reports/run.rst'
        )

    def test_output_path_honours_the_output_directory(self):
        assert export.output_path(
            'reports/run.yml', 'markdown', output_dir='out'
        ) == pathlib.Path('out/run.md')

    def test_unknown_format_raises(self, sample_document):
        with pytest.raises(export.ExportError, match='Unknown output format'):
            export.render(sample_document, 'docx')

    @pytest.mark.parametrize('output_format', TEXT_FORMATS)
    def test_every_text_format_renders_a_string(self, sample_document, output_format):
        assert isinstance(export.render(sample_document, output_format), str)

    def test_write_reports_an_unusable_path(self, tmp_path):
        with pytest.raises(export.ExportError, match='Cannot write'):
            export.write(tmp_path, 'data', 'rst')


# --- clf-export CLI ---


def _run_cli(monkeypatch, tmp_path, argv):
    """Run the export CLI and return its exit code."""
    # Keep the log file of the CLI inside the test directory.
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'log'))
    logging.getLogger('checklistfabrik').handlers.clear()

    with pytest.raises(SystemExit) as exit_info:
        ExportCli.main(['clf-export', *argv])

    return exit_info.value.code


class TestExportCli:
    def test_writes_next_to_the_report(self, monkeypatch, tmp_path, sample_report_yaml):
        code = _run_cli(
            monkeypatch, tmp_path, [str(sample_report_yaml), '--format', 'rst']
        )

        assert code == 0
        assert (tmp_path / 'report.rst').read_text().startswith('====')

    def test_format_is_inferred_from_the_output_extension(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        target = tmp_path / 'out' / 'report.md'
        target.parent.mkdir()
        code = _run_cli(
            monkeypatch, tmp_path, [str(sample_report_yaml), '--output', str(target)]
        )

        assert code == 0
        assert target.read_text().startswith('# Server Maintenance')

    def test_writes_to_stdout(self, capsys, monkeypatch, tmp_path, sample_report_yaml):
        code = _run_cli(
            monkeypatch,
            tmp_path,
            [str(sample_report_yaml), '--format', 'rst', '--output', '-'],
        )

        assert code == 0
        assert 'Server Maintenance INC-4711' in capsys.readouterr().out

    def test_output_directory_is_created(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        target_dir = tmp_path / 'exports'
        code = _run_cli(
            monkeypatch,
            tmp_path,
            [
                str(sample_report_yaml),
                '--format',
                'asciidoc',
                '--output-dir',
                str(target_dir),
            ],
        )

        assert code == 0
        assert (target_dir / 'report.adoc').is_file()

    def test_exports_a_whole_directory(self, monkeypatch, tmp_path, sample_report_yaml):
        second = tmp_path / 'second.yaml'
        second.write_text(sample_report_yaml.read_text(), encoding='utf-8')

        code = _run_cli(monkeypatch, tmp_path, [str(tmp_path), '--format', 'markdown'])

        assert code == 0
        assert (tmp_path / 'report.md').is_file()
        assert (tmp_path / 'second.md').is_file()

    def test_directory_export_skips_import_fragments(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        # A directory of checklists usually also holds files that only contain a page or
        # task list for an import.
        fragment = tmp_path / 'import-additional-tasks.yml'
        fragment.write_text(
            '- linuxfabrik.clf.html:\n    content: Fragment\n', encoding='utf-8'
        )

        code = _run_cli(monkeypatch, tmp_path, [str(tmp_path), '--format', 'rst'])

        assert code == 0
        assert (tmp_path / 'report.rst').is_file()
        assert not (tmp_path / 'import-additional-tasks.rst').exists()

    def test_metadata_can_be_switched_off(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        code = _run_cli(
            monkeypatch,
            tmp_path,
            [str(sample_report_yaml), '--format', 'rst', '--no-metadata'],
        )

        assert code == 0
        assert 'Generator' not in (tmp_path / 'report.rst').read_text()

    def test_broken_checklist_exits_non_zero(self, monkeypatch, tmp_path):
        broken = tmp_path / 'broken.yml'
        broken.write_text('title: Missing pages\n', encoding='utf-8')

        assert _run_cli(monkeypatch, tmp_path, [str(broken), '--format', 'rst']) == 1

    def test_unparsable_file_in_a_directory_exits_non_zero(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        # A file that cannot be parsed must not be silently left out of a batch export.
        broken = tmp_path / 'broken.yml'
        broken.write_text('title: T\npages:   -\n    - nope\n', encoding='utf-8')

        code = _run_cli(monkeypatch, tmp_path, [str(tmp_path), '--format', 'rst'])

        assert code == 1
        assert (tmp_path / 'report.rst').is_file()

    def test_named_import_fragment_exits_non_zero(self, monkeypatch, tmp_path):
        fragment = tmp_path / 'tasks.yml'
        fragment.write_text(
            '- linuxfabrik.clf.html:\n    content: Fragment\n', encoding='utf-8'
        )

        assert _run_cli(monkeypatch, tmp_path, [str(fragment), '--format', 'rst']) == 1

    def test_refuses_to_overwrite_the_report(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        code = _run_cli(
            monkeypatch,
            tmp_path,
            [
                str(sample_report_yaml),
                '--format',
                'rst',
                '--output',
                str(sample_report_yaml),
            ],
        )

        assert code == 1
        assert sample_report_yaml.read_text().startswith('title:')

    def test_format_is_required_when_it_cannot_be_inferred(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        assert _run_cli(monkeypatch, tmp_path, [str(sample_report_yaml)]) == 2

    def test_output_rejects_several_reports(
        self, monkeypatch, tmp_path, sample_report_yaml
    ):
        second = tmp_path / 'second.yml'
        second.write_text(sample_report_yaml.read_text(), encoding='utf-8')

        code = _run_cli(
            monkeypatch,
            tmp_path,
            [
                str(sample_report_yaml),
                str(second),
                '--format',
                'rst',
                '--output',
                str(tmp_path / 'out.rst'),
            ],
        )

        assert code == 2

    def test_missing_input_is_rejected(self, monkeypatch, tmp_path):
        assert (
            _run_cli(
                monkeypatch, tmp_path, [str(tmp_path / 'nope.yml'), '--format', 'rst']
            )
            == 2
        )


# --- dashboard export endpoint ---


@pytest.fixture()
def dashboard_client(data_mapper, sample_report_yaml):
    """Dashboard app serving the directory of the sample report."""
    directory = sample_report_yaml.parent.resolve()
    app = dashboard_wsgi_app.DashboardWsgiApp(
        directory,
        directory,
        data_mapper,
        templates.get_template_loader(),
        templates.get_assets_path(),
    )

    return werkzeug.test.Client(app), sample_report_yaml


class TestDashboardExport:
    def test_dashboard_offers_every_format(self, dashboard_client):
        client, _report = dashboard_client
        page = client.get('/').get_data(as_text=True)

        assert page.count('/export?path=') == len(export.FORMATS)
        assert 'reStructuredText' in page

    def test_export_is_served_as_a_download(self, dashboard_client):
        client, report = dashboard_client
        response = client.get(
            '/export', query_string={'format': 'rst', 'path': str(report)}
        )

        assert response.status_code == 200
        assert (
            response.headers['Content-Disposition']
            == 'attachment; filename="report.rst"'
        )
        assert 'Server Maintenance INC-4711' in response.get_data(as_text=True)

    def test_path_outside_the_reports_directory_is_forbidden(self, dashboard_client):
        client, _report = dashboard_client
        response = client.get(
            '/export', query_string={'format': 'rst', 'path': '/etc/passwd'}
        )

        assert response.status_code == 403

    def test_unknown_format_is_rejected(self, dashboard_client):
        client, report = dashboard_client
        response = client.get(
            '/export', query_string={'format': 'docx', 'path': str(report)}
        )

        assert response.status_code == 400

    def test_missing_report_is_not_found(self, dashboard_client):
        client, report = dashboard_client
        response = client.get(
            '/export',
            query_string={'format': 'rst', 'path': str(report.with_name('gone.yml'))},
        )

        assert response.status_code == 404

    def test_failed_export_reports_the_reason(self, dashboard_client, monkeypatch):
        client, report = dashboard_client

        def fail(*args, **kwargs):
            raise export.ExportError('no renderer today')

        monkeypatch.setattr(export, 'export_checklist', fail)
        response = client.get(
            '/export', query_string={'format': 'pdf', 'path': str(report)}
        )

        assert response.status_code == 500
        assert 'no renderer today' in response.get_data(as_text=True)
