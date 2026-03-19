import json
import logging
import pathlib
import threading

import jinja2
import werkzeug
import werkzeug.exceptions
import werkzeug.middleware.shared_data
import werkzeug.routing
import werkzeug.utils

from . import checklist_wsgi_app
from . import checklist_wsgi_server

HOST = '127.0.0.1'

logger = logging.getLogger(__name__)


class DashboardWsgiApp:
    """The WSGI app that powers the ChecklistFabrik dashboard."""

    def __init__(self, templates_dir, reports_dir, data_mapper, template_loader, assets_dir):
        self.assets_dir = assets_dir
        self.data_mapper = data_mapper
        self.reports_dir = reports_dir
        self.server_exit_callback = None
        self.spawned_checklists = []
        self.template_loader = template_loader
        self.templates_dir = templates_dir

        self.templ_env = jinja2.Environment(loader=template_loader)

        self.url_map = werkzeug.routing.Map(
            [
                werkzeug.routing.Rule('/', endpoint=self.on_dashboard),
                werkzeug.routing.Rule('/run', endpoint=self.on_run, methods=['POST']),
                werkzeug.routing.Rule('/view', endpoint=self.on_view, methods=['POST']),
            ],
        )

        self.wsgi_app = werkzeug.middleware.shared_data.SharedDataMiddleware(
            self.application,
            {
                '/assets': str(assets_dir),
            },
        )

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    @werkzeug.Request.application
    def application(self, request):
        urls = self.url_map.bind_to_environ(request.environ)

        try:
            endpoint, values = urls.match()
            return endpoint(request, **values)
        except werkzeug.exceptions.HTTPException as exception:
            return exception

    def cleanup(self):
        """Shut down all spawned checklist servers and save their data."""
        for _app, server, thread in self.spawned_checklists:
            if thread.is_alive():
                server.exit()
                thread.join(timeout=10)

    def scan_directory(self, directory):
        """Scan a directory for checklist YAML files and extract metadata."""
        items = []

        if not directory.is_dir():
            return items

        for path in sorted(directory.glob('*.yml')):
            try:
                data = self.data_mapper.load_yaml(path)

                if not isinstance(data, dict) or 'title' not in data or 'pages' not in data:
                    continue

                items.append({
                    'description': str(data.get('description', '')),
                    'filename': path.name,
                    'path': str(path.resolve()),
                    'title': str(data.get('title', '')),
                })
            except Exception:
                continue

        return items

    def on_dashboard(self, request, **kwargs):
        if self.templates_dir.resolve() == self.reports_dir.resolve():
            # Same directory for both: show all files in both sections.
            # The user decides whether to "Run" (new from template) or "View" (re-open).
            all_items = self.scan_directory(self.templates_dir)
            templates_list = all_items
            reports_list = all_items
        else:
            templates_list = self.scan_directory(self.templates_dir)
            reports_list = self.scan_directory(self.reports_dir)

        return werkzeug.Response(
            self.templ_env.get_template('dashboard.html.j2').render(
                reports=reports_list,
                templates=templates_list,
            ),
            mimetype='text/html',
        )

    def _launch_checklist(self, checklist_file, checklist_template, allowed_dir):
        """Launch a new checklist server and return the URL as a JSON response."""
        path = checklist_file or checklist_template

        # Security: ensure path is within allowed directory.
        if not path.resolve().is_relative_to(allowed_dir.resolve()):
            raise werkzeug.exceptions.Forbidden()

        if not path.is_file():
            raise werkzeug.exceptions.NotFound()

        try:
            app = checklist_wsgi_app.ChecklistWsgiApp(
                checklist_file,
                self.data_mapper,
                self.template_loader,
                self.assets_dir,
                checklist_template=checklist_template,
            )
        except SystemExit:
            return werkzeug.Response(
                json.dumps({'error': 'Failed to load checklist'}),
                status=500,
                mimetype='application/json',
            )

        server = checklist_wsgi_server.ChecklistWsgiServer(HOST, 0, app)
        host, port = server.server_address

        def serve_and_save():
            server.serve(open_browser=False)
            app.save_checklist()

        thread = threading.Thread(target=serve_and_save, daemon=True)
        thread.start()

        self.spawned_checklists.append((app, server, thread))

        return werkzeug.Response(
            json.dumps({'url': f'http://{host}:{port}'}),
            mimetype='application/json',
        )

    def _parse_path_from_request(self, request):
        """Extract and validate the path from a JSON request body."""
        try:
            data = json.loads(request.data)
        except json.JSONDecodeError:
            raise werkzeug.exceptions.BadRequest()

        path = data.get('path')

        if not path:
            raise werkzeug.exceptions.BadRequest()

        return path

    def on_run(self, request, **kwargs):
        """Start a new checklist from a template."""
        template_path = self._parse_path_from_request(request)

        return self._launch_checklist(
            checklist_file=None,
            checklist_template=pathlib.Path(template_path),
            allowed_dir=self.templates_dir,
        )

    def on_view(self, request, **kwargs):
        """Open an existing report for viewing or re-playing."""
        report_path = self._parse_path_from_request(request)

        return self._launch_checklist(
            checklist_file=pathlib.Path(report_path),
            checklist_template=None,
            allowed_dir=self.reports_dir,
        )
