import argparse
import logging
import pathlib
import webbrowser

import ruamel.yaml

from .base_cli import BaseCli
from .. import checklist_data_mapper
from .. import checklist_wsgi_app
from .. import checklist_wsgi_server
from .. import templates

DESCRIPTION = (
    'Interactive CLI for launching dynamic, web-based checklists. '
    'Leverage YAML templates with Jinja logic to create, run, and track recurring procedures.'
)
HOST = 'localhost'
PORT = 9309

logger = logging.getLogger(__name__)

__author__ = 'Linuxfabrik GmbH, Zurich/Switzerland'
__version__ = '2025032801'


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
            '-V', '--version',
            help='Display the program\'s version information and exit.',
            action='version',
            version=f'%(prog)s: v{__version__} by {__author__}'
        )

        self.arg_parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Optional: Also log debug messages on console.',
        )

        self.arg_parser.add_argument(
            'file',
            help=(
                'Path to the checklist file. If the file exists, it will be loaded for re-running. '
                'If you want to create a new checklist, provide a non-existent file path and use '
                'the `--template` option.'
            ),
            type=pathlib.Path,
        )

        self.arg_parser.add_argument(
            '--force',
            action='store_true',
            help=(
                'Allow creating a checklist from a template even if the target checklist file '
                '(the `file` argument) already exists. '
                'WARNING: THE TARGET FILE WILL BE OVERWRITTEN.'
            ),
        )

        self.arg_parser.add_argument(
            '--open',
            action=argparse.BooleanOptionalAction,
            help='Control whether to open the checklist page the default browser.',
            default=True,
        )

        self.arg_parser.add_argument(
            '--template',
            help=(
                'Optional: Path to a YAML template file for creating a new checklist. '
                'This option may only be used when the target checklist file (the `file` '
                'argument) does not already exist or the `--force` option is used.'
            ),
            type=pathlib.Path,
        )

    def validate_args(self):
        if self.args.template is not None:
            if self.args.file.is_file() and not self.args.force:
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

        checklist_server = checklist_wsgi_server.ChecklistWsgiServer(HOST, PORT, checklist_app)

        if self.args.open:
            webbrowser.open(f'http://{HOST}:{PORT}')

        checklist_server.serve()

        checklist_app.save_checklist()

        return 0


def main(args=None):
    PlayCli.main(args)


if __name__ == '__main__':
    main()
