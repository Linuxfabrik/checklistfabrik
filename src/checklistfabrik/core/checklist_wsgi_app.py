import datetime
import json
import logging
import os.path
import pathlib
import uuid

import jinja2
import werkzeug
import werkzeug.exceptions
import werkzeug.middleware.shared_data
import werkzeug.routing
import werkzeug.utils

from . import markdown

TEMPLATE_STRING = '''\
{% extends "checklist.html.j2" %}
{% block form_content %}
{{data}}
{% endblock %}
'''

logger = logging.getLogger(__name__)

# Global Jinja variables for use in templates
jinja_globals = {
    'now': datetime.datetime.now,
}


class ChecklistWsgiApp:
    """The WSGI app that powers the ChecklistFabrik HTML interface."""

    def __init__(self, checklist_file, checklist_mapper, template_loader, assets_dir, checklist_template=None):
        self.checklist_file = checklist_file
        self.checklist_mapper = checklist_mapper
        self.checklist_template = checklist_template
        self.server_exit_callback = None

        self.server_id = uuid.uuid4().hex
        self.templ_env = jinja2.Environment(loader=template_loader)
        self.markdown = markdown.create_markdown()

        self.templ_env.globals.update(jinja_globals)

        self.url_map = werkzeug.routing.Map(
            [
                werkzeug.routing.Rule('/', endpoint=lambda request: werkzeug.utils.redirect('/page/0')),
                werkzeug.routing.Rule('/done', endpoint=self.on_done),
                werkzeug.routing.Rule('/exit', endpoint=self.on_exit),
                werkzeug.routing.Rule('/heartbeat', endpoint=self.on_heartbeat),
                werkzeug.routing.Rule('/page/', endpoint=lambda request: werkzeug.utils.redirect('/page/0')),
                werkzeug.routing.Rule('/page/<int:id>', endpoint=self.on_page),
                werkzeug.routing.Rule('/page/<int:id>/next', endpoint=self.on_next_page),
                werkzeug.routing.Rule('/page/<int:id>/prev', endpoint=self.on_prev_page),
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
            # Loaded from this file, now write to it again.
            self.checklist_mapper.save_checklist(self.checklist_file, self.checklist)
            return

        # No file was specified, neither on the CLI nor in the template file, so generate one.

        # Try to generate filename based on the template's report path.
        if self.checklist.report_path:
            generated_filename = self.templ_env.from_string(self.checklist.report_path).render(self.checklist.facts)

            # Remove well-known invalid characters for the most commonly used operating systems and filesystems.
            clean_filename = generated_filename.translate(
                str.maketrans(
                    {
                        ctrl_char: None for ctrl_char in range(0, 32)
                    } | {
                        '"': None,
                        '*': None,
                        ':': None,
                        '<': None,
                        '>': None,
                        '?': None,
                    }
                )
            )

            file_to_save = pathlib.Path(os.path.expandvars(clean_filename))
            logger.info('Generated file path based on template: "%s"', file_to_save)
        else:
            file_to_save = pathlib.Path(f'checklist_{datetime.date.today().isoformat()}.yml')
            logger.warning('No file name set. Falling back to "%s"', file_to_save)

        # Saving to the file with the generated file name.
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
        page_id = kwargs['id']

        if page_id >= len(self.checklist):  # page_id will always be an unsigned integer due to Werkzeug's IntegerConverter.
            raise werkzeug.exceptions.NotFound()

        if request.method == 'POST':
            redirect = ''

            for key in request.form.keys():
                if key == 'submit_action':
                    redirect = request.form.get(key, '').lower()
                    continue

                if key.endswith('[]'):
                    # List keys are marked with '[]' to differentiate them from single value keys,
                    # otherwise it would be impossible to differentiate single values from lists with exactly one value (due to how HTML forms work).
                    self.checklist.facts[key[:-2]] = [
                        value
                        for value in request.form.getlist(key)
                        # Only save if non-empty. An empty string is used to force the HTML form to send empty selections/states.
                        # This was implemented as otherwise it would be impossible to change an already submitted value
                        # to be blank (e.g. unchecking a checkbox) as the HTML form does not send empty inputs.
                        if value
                    ]
                else:
                    value = request.form.get(key)

                    # Only save if non-empty, otherwise reset. An empty string is used to force the HTML form to send
                    # empty selections/states. This was implemented as otherwise it would be impossible to change an already
                    # submitted value to be blank (e.g. unchecking a checkbox) as the HTML form does not send empty inputs.
                    self.checklist.facts[key] = value if value else None

            if redirect == 'save and exit':
                return werkzeug.utils.redirect(f'/exit')

            if redirect == 'next':
                return werkzeug.utils.redirect(f'/page/{page_id}/next')

        page_data = self.checklist.pages[page_id].render(self.checklist.facts, self.templ_env, self.markdown)

        return werkzeug.Response(
            self.templ_env.from_string(TEMPLATE_STRING).render(
                title=self.checklist.title,
                version=self.checklist.version,
                page_id=page_id,
                data=page_data,
                pages=[
                    {
                        'id': id,
                        'title': page.title,
                        'eval_when': page.eval_when(self.checklist.facts)[0],
                    }
                    for id, page in enumerate(self.checklist.pages)
                ],
                server_id=self.server_id,
            ),
            mimetype='text/html',
        )

    def on_next_page(self, request, **kwargs):
        page_id = kwargs['id']

        # Find the next applicable page.
        next_page_id = page_id + 1
        while next_page_id < len(self.checklist):
            if self.checklist.pages[next_page_id].eval_when(self.checklist.facts)[0]:
                break

            next_page_id += 1
        else:
            return werkzeug.utils.redirect(f'/done')

        return werkzeug.utils.redirect(f'/page/{next_page_id}')

    def on_prev_page(self, request, **kwargs):
        page_id = kwargs['id']

        return werkzeug.utils.redirect(f'/page/{max(0, page_id - 1)}')

    def on_done(self, request, **kwargs):
        return werkzeug.Response(
            self.templ_env.get_template('done.html.j2').render(
                last_page_id=len(self.checklist) - 1,
            ),
            mimetype='text/html',
        )

    def on_exit(self, request, **kwargs):
        if self.server_exit_callback is None or not callable(self.server_exit_callback):
            raise werkzeug.exceptions.NotImplemented()

        self.server_exit_callback()

        return werkzeug.Response(self.templ_env.get_template('shutdown.html.j2').render(), mimetype='text/html')

    def on_heartbeat(self, request, **kwargs):
        return werkzeug.Response(json.dumps({'server_id': self.server_id}), mimetype='application/json')
