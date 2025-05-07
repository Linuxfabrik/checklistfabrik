import argparse
import logging
import pathlib

import ruamel.yaml

from .base_cli import BaseCli, IntRange
from .. import __version__
from .. import checklist_data_mapper
from .. import checklist_wsgi_app
from .. import checklist_wsgi_server
from .. import templates

DESCRIPTION = (
    'Interactive CLI for launching dynamic, web-based checklists. '
    'Leverage YAML templates with Jinja logic to create, run, and track recurring procedures.'
)
HOST = '127.0.0.1'

logger = logging.getLogger(__name__)

__author__ = 'Linuxfabrik GmbH, Zurich/Switzerland'


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
            'report_file',
            help=(
                'Path to the report file. If the file exists, it will be loaded for re-running. '
                'If you want to create a new report from an existing checklist/template, '
                'provide a non-existent file path and use the `--template` option. '
                'This option may be left empty to auto-generate the file path '
                'based on the template\'s `report_path` (if provided) or simply a timestamp.'
            ),
            nargs='?',
            type=pathlib.Path,
        )

        self.arg_parser.add_argument(
            '--force',
            action='store_true',
            help=(
                'Allow creating a checklist from a template even if the report checklist file '
                '(the `report_file` argument) already exists. '
                'WARNING: THE REPORT FILE WILL BE OVERWRITTEN.'
            ),
        )

        self.arg_parser.add_argument(
            '--open',
            action=argparse.BooleanOptionalAction,
            help='Control whether to open the checklist page the default browser.',
            default=True,
        )

        self.arg_parser.add_argument(
            '--port',
            help='Port to use for the HTTP server. Using "0" will auto-select an available port. Default: %(default)d',
            default=0,
            type=IntRange(0, 65536),
        )

        self.arg_parser.add_argument(
            '--template',
            help=(
                'Optional: Path to a YAML template file for creating a new report. '
                'This option may only be used when the report file (the `report_file` '
                'argument) does not already exist or the `--force` option is used.'
            ),
            type=pathlib.Path,
        )

    def validate_args(self):
        if self.args.template is not None:
            if self.args.report_file and self.args.report_file.is_file() and not self.args.force:
                self.arg_parser.error('--template may only be specified if the report file does not exist')

            if not self.args.template.is_file():
                self.arg_parser.error('--template must be a file')

        else:
            if not (self.args.report_file and self.args.report_file.is_file()):
                self.arg_parser.error('report file must exist')

    def run(self):

        checklist_app = checklist_wsgi_app.ChecklistWsgiApp(
            self.args.report_file,
            self.data_mapper,
            templates.get_template_loader(),
            templates.get_assets_path(),
            checklist_template=self.args.template,
        )

        checklist_server = checklist_wsgi_server.ChecklistWsgiServer(HOST, self.args.port, checklist_app)

        checklist_server.serve(open_browser=self.args.open)

        checklist_app.save_checklist()

        return 0


def main(args=None):
    PlayCli.main(args)
