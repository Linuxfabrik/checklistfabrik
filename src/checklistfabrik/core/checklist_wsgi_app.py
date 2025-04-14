import datetime
import json
import logging
import pathlib
import urllib.parse
import uuid

import jinja2
import werkzeug
import werkzeug.exceptions
import werkzeug.middleware.shared_data
import werkzeug.routing
import werkzeug.utils

TEMPLATE_STRING = '''\
{% extends "checklist.html.j2" %}
{% block form_content %}
{{data}}
{% endblock %}
'''

logger = logging.getLogger(__name__)


class ChecklistWsgiApp:
    """The WSGI app that powers the ChecklistFabrik HTML interface."""

    def __init__(self, checklist_file, checklist_mapper, template_loader, assets_dir, checklist_template=None):
        self.checklist_file = checklist_file
        self.checklist_mapper = checklist_mapper
        self.checklist_template = checklist_template
        self.server_exit_callback = None

        self.server_id = uuid.uuid4().hex
        self.templ_env = jinja2.Environment(loader=template_loader)

        self.url_map = werkzeug.routing.Map(
            [
                werkzeug.routing.Rule('/', endpoint=lambda request: werkzeug.utils.redirect('page')),
                werkzeug.routing.Rule('/exit', endpoint=self.on_exit),
                werkzeug.routing.Rule('/heartbeat', endpoint=self.on_heartbeat),
                werkzeug.routing.Rule('/page', endpoint=self.on_page),
            ],
        )

        self.wsgi_app = werkzeug.middleware.shared_data.SharedDataMiddleware(
            self.application,
            {
                '/assets': str(assets_dir),
            },
        )

        self.checklist = self.load_checklist()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def load_checklist(self):
        file_to_load = self.checklist_template if self.checklist_template is not None else self.checklist_file

        return self.checklist_mapper.load_checklist(file_to_load)

    def save_checklist(self):
        if self.checklist_file:
            # Loaded from this file now save to it.
            self.checklist_mapper.save_checklist(self.checklist_file, self.checklist)
            return

        # No filename was specified, neither on the CLI nor in the template file, so generate one.

        # Try to generate filename based on the templates target filename
        if self.checklist.target_filename:
            generated_filename = jinja2.Template(self.checklist.target_filename).render(self.checklist.facts)

            # Remove well-known invalid characters for the most commonly used operating systems and filesystems.
            clean_filename = generated_filename.translate(
                str.maketrans(
                    {
                        ctrl_char: None for ctrl_char in range(0, 32)
                    } | {
                        '"': None,
                        '*': None,
                        '/': None,
                        ':': None,
                        '<': None,
                        '>': None,
                        '?': None,
                        '\\': None,
                    }
                )
            )

            file_to_save = pathlib.Path(f'{clean_filename}.yml')
            logger.info('Generated file name based on template: "%s"', file_to_save)
        else:
            file_to_save = pathlib.Path(f'checklist_{datetime.datetime.now().isoformat(timespec="milliseconds")}.yml')
            logger.warning('No file name set. Falling back to "%s"', file_to_save)

        # Saving to the file with the generated filename.
        # This should never overwrite already existing files with the same name.
        self.checklist_mapper.save_checklist(file_to_save, self.checklist, overwrite=False)

    @werkzeug.Request.application
    def application(self, request):
        urls = self.url_map.bind_to_environ(request.environ)

        try:
            endpoint, values = urls.match()
            return endpoint(request, **values)
        except werkzeug.exceptions.HTTPException as exception:
            return exception

    def on_page(self, request, **kwargs):
        quoted_page_name = request.args.get('name')

        if not quoted_page_name:
            first_page_name = self.checklist.first_page_name()

            if first_page_name is None:
                raise werkzeug.exceptions.NotFound()

            return werkzeug.utils.redirect(f'/page?name={urllib.parse.quote(first_page_name, safe="")}')

        page_name = urllib.parse.unquote(quoted_page_name)

        next_page_name = self.checklist.next_page_name(page_name)
        prev_page_name = self.checklist.prev_page_name(page_name)
        quoted_next_page_name = urllib.parse.quote(next_page_name, safe="") if next_page_name is not None else None
        quoted_prev_page_name = urllib.parse.quote(prev_page_name, safe="") if prev_page_name is not None else None

        if page_name is None:
            raise werkzeug.exceptions.NotFound()

        current_page = self.checklist.pages.get(page_name)

        if current_page is None:
            raise werkzeug.exceptions.NotFound()

        if request.method == 'POST':
            redirect_next = False

            for key in request.form.keys():
                if key == 'submit_action' and request.form.get(key, '').lower() == 'next':
                    redirect_next = True
                    continue

                if key.endswith('[]'):
                    # List keys are marked with '[]' to differentiate them from single value keys,
                    # otherwise it would be impossible to differentiate single values from lists with exactly one value (due to how HTML forms work).
                    self.checklist.facts[key[:-2]] = request.form.getlist(key)
                else:
                    self.checklist.facts[key] = request.form.get(key)

            if redirect_next:
                return werkzeug.utils.redirect(f'/page?name={quoted_next_page_name}')

        page_data = current_page.render(self.checklist.facts)

        return werkzeug.Response(
            self.templ_env.from_string(TEMPLATE_STRING).render(
                title=self.checklist.title,
                version=self.checklist.version,
                next_task_name=quoted_next_page_name,
                prev_task_name=quoted_prev_page_name,
                data=page_data,
                server_id=self.server_id,
            ),
            mimetype='text/html',
        )

    def on_exit(self, request, **kwargs):
        if self.server_exit_callback is None or not callable(self.server_exit_callback):
            raise werkzeug.exceptions.NotImplemented()

        self.server_exit_callback()

        return werkzeug.Response('<h1>Shutting down server</h1><p>You can now close this page.</p>', mimetype='text/html')

    def on_heartbeat(self, request, **kwargs):
        return werkzeug.Response(json.dumps({'server_id': self.server_id}), mimetype='application/json')
