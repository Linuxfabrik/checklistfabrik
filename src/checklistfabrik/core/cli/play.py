import logging
import pathlib
import webbrowser

import ruamel.yaml

from .base_cli import BaseCli
from .. import checklist_data_mapper
from .. import checklist_wsgi_app
from .. import checklist_wsgi_server
from .. import templates

DESCRIPTION = 'ChecklistFabrik Play'
HOST = 'localhost'
PORT = 9309

logger = logging.getLogger(__name__)


class PlayCli(BaseCli):
    """The ChecklistFabrik play CLI."""

    def __init__(self):
        super().__init__(DESCRIPTION)

        self.yaml = ruamel.yaml.YAML()

        self.yaml.preserve_quotes = True
        self.yaml.block_seq_indent = 2
        self.yaml.map_indent = 2
        self.yaml.sequence_indent = 4

        self.data_mapper = checklist_data_mapper.ChecklistDataMapper(self.yaml)

    def init_args(self):
        self.arg_parser.add_argument(
            'file',
            type=pathlib.Path,
        )

        self.arg_parser.add_argument(
            '--template',
            type=pathlib.Path,
        )

    def validate_args(self):
        if self.args.template is not None:
            if self.args.file.is_file():
                self.arg_parser.error('--template may only be specified if file does not exist')

            if not self.args.template.is_file():
                self.arg_parser.error('--template must be a file')

        else:
            if not self.args.file.is_file():
                self.arg_parser.error('file must exist')

    def run(self):

        checklist_app = checklist_wsgi_app.ChecklistWsgiApp(
            self.args.file,
            self.data_mapper,
            templates.get_template_loader(),
            templates.get_assets_path(),
            checklist_template=self.args.template,
        )

        webbrowser.open(f'http://{HOST}:{PORT}')

        checklist_server = checklist_wsgi_server.ChecklistWsgiServer(HOST, PORT, checklist_app)

        checklist_server.serve()

        checklist_app.save_checklist()

        return 0


def main(args=None):
    PlayCli.main(args)


if __name__ == '__main__':
    main()
