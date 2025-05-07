import logging
import webbrowser
import wsgiref.simple_server

logger = logging.getLogger(__name__)


class ChecklistWsgiRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    """A variant of the WSGIRequestHandler that logs messages using the logging package."""

    def log_message(self, format, *args):
        if not 'GET /heartbeat HTTP/1.1' in args:
            logger.debug(format, *args)


class ChecklistWsgiServer(wsgiref.simple_server.WSGIServer):
    """The WSGI server that powers the ChecklistFabrik HTML interface."""

    def __init__(self, host, port, application):
        self.exit_flag = False

        super().__init__((host, port), ChecklistWsgiRequestHandler)

        self.set_app(application)

        application.server_exit_callback = self.exit

    def exit(self):
        self.exit_flag = True

    def serve(self, open_browser=False):
        host, port = self.server_address

        logger.info('Starting server on "http://%s:%d"', host, port)

        print('Press Ctrl+C to shutdown the server and save the checklist to disk.')

        if open_browser:
            webbrowser.open(f'http://{host}:{port}')

        try:
            while not self.exit_flag:
                self.handle_request()
        except KeyboardInterrupt:
            pass
        finally:
            logger.info('Shutting down server')
            self.server_close()
