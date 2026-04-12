"""Tests for checklistfabrik.core.checklist_data_mapper."""

import textwrap

import pytest

from checklistfabrik.core.checklist_data_mapper import ChecklistLoadError
from checklistfabrik.core.models.checklist import Checklist


class TestLoadYaml:
    def test_load_valid_file(self, data_mapper, tmp_path):
        f = tmp_path / 'test.yml'
        f.write_text('key: value\n', encoding='utf-8')
        result = data_mapper.load_yaml(f)
        assert result == {'key': 'value'}

    def test_load_nonexistent_file(self, data_mapper, tmp_path):
        with pytest.raises(ChecklistLoadError):
            data_mapper.load_yaml(tmp_path / 'missing.yml')

    def test_load_directory(self, data_mapper, tmp_path):
        with pytest.raises(ChecklistLoadError):
            data_mapper.load_yaml(tmp_path)


class TestProcessChecklist:
    def test_minimal_checklist(self, data_mapper):
        data = {
            'title': 'Test',
            'pages': [
                {
                    'title': 'P1',
                    'tasks': [
                        {'linuxfabrik.clf.html': {'content': 'hello'}},
                    ],
                },
            ],
        }
        checklist = data_mapper.process_checklist(data, '.')
        assert isinstance(checklist, Checklist)
        assert checklist.title == 'Test'
        assert len(checklist) == 1

    def test_checklist_with_optional_fields(self, data_mapper):
        data = {
            'title': 'Test',
            'description': 'A test checklist',
            'report_path': 'reports/report.yml',
            'version': '1.0',
            'pages': [
                {
                    'title': 'P1',
                    'tasks': [
                        {'linuxfabrik.clf.html': {'content': 'x'}},
                    ],
                },
            ],
        }
        checklist = data_mapper.process_checklist(data, '.')
        assert checklist.description == 'A test checklist'
        assert checklist.report_path == 'reports/report.yml'
        assert checklist.version == '1.0'

    def test_empty_checklist_raises(self, data_mapper):
        with pytest.raises(ValueError, match='empty'):
            data_mapper.process_checklist(None, '.')

    def test_missing_title_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist({'pages': []}, '.')

    def test_missing_pages_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist({'title': 'T'}, '.')

    def test_extra_keys_raise(self, data_mapper):
        data = {'title': 'T', 'pages': [], 'unknown': True}
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist(data, '.')

    def test_non_string_title_raises(self, data_mapper):
        data = {'title': 123, 'pages': []}
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist(data, '.')

    def test_non_list_pages_raises(self, data_mapper):
        data = {'title': 'T', 'pages': 'not a list'}
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist(data, '.')

    def test_non_string_description_raises(self, data_mapper):
        data = {'title': 'T', 'pages': [], 'description': 123}
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_checklist(data, '.')


class TestProcessPage:
    def test_valid_page(self, data_mapper):
        page_data = {
            'title': 'My Page',
            'tasks': [
                {'linuxfabrik.clf.html': {'content': 'x'}},
            ],
        }
        page = data_mapper.process_page(page_data, '.', {})
        assert page.title == 'My Page'
        assert len(page.tasks) == 1

    def test_page_with_when(self, data_mapper):
        page_data = {
            'title': 'Conditional',
            'tasks': [],
            'when': 'x == 1',
        }
        page = data_mapper.process_page(page_data, '.', {})
        assert page.when == 'x == 1'

    def test_missing_title_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_page({'tasks': []}, '.', {})

    def test_empty_title_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_page({'title': '', 'tasks': []}, '.', {})

    def test_non_list_tasks_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_page({'title': 'P', 'tasks': 'nope'}, '.', {})


class TestProcessTaskList:
    def test_task_with_fact_name(self, data_mapper):
        task_data = [
            {
                'linuxfabrik.clf.text_input': {'label': 'Name'},
                'fact_name': 'user_name',
            },
        ]
        facts = {}
        tasks = data_mapper.process_task_list(task_data, '.', facts)
        assert len(tasks) == 1
        assert tasks[0].fact_name == 'user_name'

    def test_task_with_value(self, data_mapper):
        task_data = [
            {
                'linuxfabrik.clf.text_input': {'label': 'Name'},
                'fact_name': 'user_name',
                'value': 'default',
            },
        ]
        facts = {}
        data_mapper.process_task_list(task_data, '.', facts)
        assert facts['user_name'] == 'default'

    def test_task_with_when(self, data_mapper):
        task_data = [
            {
                'linuxfabrik.clf.html': {'content': 'x'},
                'when': 'show == true',
            },
        ]
        tasks = data_mapper.process_task_list(task_data, '.', {})
        assert tasks[0].when == 'show == true'

    def test_invalid_fact_name_bracket_suffix_raises(self, data_mapper):
        task_data = [
            {
                'linuxfabrik.clf.text_input': {'label': 'x'},
                'fact_name': 'bad_name[]',
            },
        ]
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_task_list(task_data, '.', {})

    def test_empty_task_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_task_list([{}], '.', {})

    def test_non_dict_task_raises(self, data_mapper):
        with pytest.raises(ChecklistLoadError):
            data_mapper.process_task_list(['not a dict'], '.', {})


class TestSaveChecklist:
    def test_save_and_reload(self, data_mapper, tmp_path):
        data = {
            'title': 'Roundtrip',
            'pages': [
                {
                    'title': 'P1',
                    'tasks': [
                        {'linuxfabrik.clf.html': {'content': 'hi'}},
                    ],
                },
            ],
        }
        checklist = data_mapper.process_checklist(data, '.')
        out_file = tmp_path / 'output.yml'
        data_mapper.save_checklist(out_file, checklist)

        assert out_file.exists()
        reloaded = data_mapper.load_yaml(out_file)
        assert reloaded['title'] == 'Roundtrip'

    def test_save_no_overwrite(self, data_mapper, tmp_path):
        data = {
            'title': 'T',
            'pages': [
                {
                    'title': 'P1',
                    'tasks': [
                        {'linuxfabrik.clf.html': {'content': 'x'}},
                    ],
                },
            ],
        }
        checklist = data_mapper.process_checklist(data, '.')

        out_file = tmp_path / 'report.yml'
        out_file.write_text('existing', encoding='utf-8')

        data_mapper.save_checklist(out_file, checklist, overwrite=False)

        # Original file should be untouched.
        assert out_file.read_text(encoding='utf-8') == 'existing'
        # A new file with suffix should exist.
        assert (tmp_path / 'report_1.yml').exists()


class TestPageImport:
    def test_import_pages(self, data_mapper, tmp_path):
        imported_pages = textwrap.dedent("""\
            - title: Imported Page
              tasks:
                - linuxfabrik.clf.html:
                      content: imported content
        """)
        import_file = tmp_path / 'pages.yml'
        import_file.write_text(imported_pages, encoding='utf-8')

        checklist_data = {
            'title': 'With Import',
            'pages': [
                {'linuxfabrik.clf.import': str(import_file)},
            ],
        }
        checklist = data_mapper.process_checklist(checklist_data, tmp_path)
        assert len(checklist) == 1
        assert checklist.pages[0].title == 'Imported Page'

    def test_import_tasks(self, data_mapper, tmp_path):
        imported_tasks = textwrap.dedent("""\
            - linuxfabrik.clf.html:
                  content: from import
        """)
        import_file = tmp_path / 'tasks.yml'
        import_file.write_text(imported_tasks, encoding='utf-8')

        page_data = {
            'title': 'Page with imported tasks',
            'tasks': [
                {'linuxfabrik.clf.import': str(import_file)},
            ],
        }
        facts = {}
        page = data_mapper.process_page(page_data, tmp_path, facts)
        assert len(page.tasks) == 1
