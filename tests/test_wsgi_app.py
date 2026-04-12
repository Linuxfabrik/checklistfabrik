"""Tests for checklistfabrik.core.checklist_wsgi_app."""

import textwrap

import jinja2
import werkzeug.test

from checklistfabrik.core.checklist_wsgi_app import ChecklistWsgiApp

from .conftest import TEMPLATES_DIR


def _create_app(tmp_path, checklist_yaml=None):
    """Create a ChecklistWsgiApp from a YAML string for testing."""
    if checklist_yaml is None:
        checklist_yaml = textwrap.dedent("""\
            title: Test Checklist
            pages:
              - title: First Page
                tasks:
                  - linuxfabrik.clf.html:
                        content: Page one content
              - title: Second Page
                tasks:
                  - linuxfabrik.clf.html:
                        content: Page two content
              - title: Conditional Page
                when: show_page3 == true
                tasks:
                  - linuxfabrik.clf.html:
                        content: Conditional content
        """)

    checklist_file = tmp_path / 'checklist.yml'
    checklist_file.write_text(checklist_yaml, encoding='utf-8')

    import ruamel.yaml

    from checklistfabrik.core.checklist_data_mapper import ChecklistDataMapper

    yaml = ruamel.yaml.YAML()
    mapper = ChecklistDataMapper(yaml)
    loader = jinja2.FileSystemLoader(str(TEMPLATES_DIR))
    assets_dir = TEMPLATES_DIR / 'assets'

    app = ChecklistWsgiApp(checklist_file, mapper, loader, assets_dir)
    return app


class TestChecklistWsgiApp:
    def test_root_redirects_to_page_0(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/')
        assert response.status_code == 302
        assert '/page/0' in response.headers['Location']

    def test_page_get(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/page/0')
        assert response.status_code == 200
        assert 'Page one content' in response.get_data(as_text=True)

    def test_page_not_found(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/page/999')
        assert response.status_code == 404

    def test_page_post_saves_facts(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.post(
            '/page/0',
            data={
                'submit_action': 'next',
                'my_fact': 'my_value',
            },
        )
        assert response.status_code == 302
        assert app.checklist.facts['my_fact'] == 'my_value'

    def test_page_post_list_values(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        client.post(
            '/page/0',
            data={
                'submit_action': '',
                'items[]': ['a', 'b', ''],
            },
        )
        assert app.checklist.facts['items'] == ['a', 'b']

    def test_page_post_empty_value_resets(self, tmp_path):
        app = _create_app(tmp_path)
        app.checklist.facts['key'] = 'old_value'
        client = werkzeug.test.Client(app)
        client.post(
            '/page/0',
            data={
                'submit_action': '',
                'key': '',
            },
        )
        assert app.checklist.facts['key'] is None

    def test_next_page(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/page/0/next')
        assert response.status_code == 302
        assert '/page/1' in response.headers['Location']

    def test_next_page_skips_hidden(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        # Page 2 has when condition, should be skipped -> done
        response = client.get('/page/1/next')
        assert response.status_code == 302
        assert '/done' in response.headers['Location']

    def test_prev_page(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/page/1/prev')
        assert response.status_code == 302
        assert '/page/0' in response.headers['Location']

    def test_done_page(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/done')
        assert response.status_code == 200

    def test_heartbeat(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.get('/heartbeat')
        assert response.status_code == 200
        assert 'server_id' in response.get_data(as_text=True)

    def test_page_post_redirect_previous(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.post(
            '/page/1',
            data={
                'submit_action': 'previous',
            },
        )
        assert response.status_code == 302
        assert '/prev' in response.headers['Location']

    def test_page_post_redirect_page_jump(self, tmp_path):
        app = _create_app(tmp_path)
        client = werkzeug.test.Client(app)
        response = client.post(
            '/page/0',
            data={
                'submit_action': 'page 1',
            },
        )
        assert response.status_code == 302
        assert '/page/1' in response.headers['Location']

    def test_save_and_exit(self, tmp_path):
        app = _create_app(tmp_path)
        exit_called = []
        app.server_exit_callback = lambda: exit_called.append(True)
        client = werkzeug.test.Client(app)
        response = client.get('/exit')
        assert response.status_code == 200
        assert len(exit_called) == 1

    def test_checklist_title_is_html_escaped(self, tmp_path):
        """Malicious YAML with a script tag in the checklist title must be escaped."""
        payload = "<script>alert('xss')</script>"
        checklist_yaml = textwrap.dedent(f"""\
            title: "{payload}"
            pages:
              - title: Safe Page
                tasks:
                  - linuxfabrik.clf.html:
                        content: Safe content
        """)
        app = _create_app(tmp_path, checklist_yaml=checklist_yaml)
        client = werkzeug.test.Client(app)
        response = client.get('/page/0')
        body = response.get_data(as_text=True)
        assert payload not in body
        assert '&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;' in body

    def test_page_title_is_html_escaped(self, tmp_path):
        """Malicious YAML with a script tag in a page title must be escaped."""
        payload = "<script>alert('xss')</script>"
        checklist_yaml = textwrap.dedent(f"""\
            title: Test
            pages:
              - title: "{payload}"
                tasks:
                  - linuxfabrik.clf.html:
                        content: Safe content
        """)
        app = _create_app(tmp_path, checklist_yaml=checklist_yaml)
        client = werkzeug.test.Client(app)
        response = client.get('/page/0')
        body = response.get_data(as_text=True)
        assert payload not in body
        assert '&lt;script&gt;' in body
