"""Spawn child ChecklistFabrik servers from inside another WSGI app.

Both the dashboard and a running checklist can launch new checklists in
separate threads and return a URL that the browser opens in a new tab.
This module centralises that logic so the same code path is used in both
places.
"""

import json
import logging
import threading

import werkzeug
import werkzeug.exceptions

from . import checklist_wsgi_app, checklist_wsgi_server

HOST = '127.0.0.1'

logger = logging.getLogger(__name__)


def launch_checklist(
    checklist_file,
    checklist_template,
    data_mapper,
    template_loader,
    assets_dir,
    spawned_checklists,
    allowed_dir=None,
):
    """Launch a checklist server in a daemon thread and return its URL as JSON.

    The caller passes its own ``spawned_checklists`` list so each WSGI app
    can shut down its own children on exit.

    If ``allowed_dir`` is set, the target file must live inside that directory
    (used by the dashboard to restrict to ``templates_dir``/``reports_dir``).
    If ``allowed_dir`` is ``None``, only file existence is enforced.
    """
    path = checklist_file or checklist_template

    if allowed_dir is not None and not path.resolve().is_relative_to(allowed_dir.resolve()):
        raise werkzeug.exceptions.Forbidden()

    if not path.is_file():
        raise werkzeug.exceptions.NotFound()

    try:
        app = checklist_wsgi_app.ChecklistWsgiApp(
            checklist_file,
            data_mapper,
            template_loader,
            assets_dir,
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
        # Stop any grand-children spawned through this checklist before saving,
        # so their save_checklist runs before this server returns.
        app.cleanup()
        app.save_checklist()

    thread = threading.Thread(target=serve_and_save, daemon=True)
    thread.start()

    spawned_checklists.append((app, server, thread))

    return werkzeug.Response(
        json.dumps({'url': f'http://{host}:{port}'}),
        mimetype='application/json',
    )


def cleanup_spawned_checklists(spawned_checklists):
    """Stop all spawned checklist servers and join their threads."""
    for _app, server, thread in spawned_checklists:
        if thread.is_alive():
            server.exit()
            thread.join(timeout=10)
