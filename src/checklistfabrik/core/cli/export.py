import logging
import pathlib
import sys

import ruamel.yaml

from .. import __version__, checklist_data_mapper, export
from .base_cli import BaseCli

DESCRIPTION = (
    'Non-interactive CLI for exporting checklist reports into static documents. '
    'Converts a YAML report into AsciiDoc, HTML, Markdown, PDF or reStructuredText '
    'so it can be committed, reviewed in a pull request or published as documentation. '
    'The YAML report itself is never modified.'
)

#: Extensions the batch mode picks up when a directory is exported. Matches the file
#: extensions the dashboard scans for.
REPORT_SUFFIXES = ('*.yaml', '*.yml')

#: Value of `--output` that writes the exported document to stdout.
STDOUT_TARGET = '-'

logger = logging.getLogger(__name__)

__author__ = 'Linuxfabrik GmbH, Zurich/Switzerland'


class ExportCli(BaseCli):
    """The ChecklistFabrik export CLI."""

    BANNER = f'ChecklistFabrik v{__version__}'

    def __init__(self):
        super().__init__(DESCRIPTION)

        self.output_format = None
        # Files of a scanned directory are parsed once to tell checklists from import
        # fragments. The result is kept so the export does not read them a second time.
        self.parsed = {}
        self.sources = []
        self.unparsable = set()
        self.yaml = ruamel.yaml.YAML()

        self.yaml.preserve_quotes = True

        self.data_mapper = checklist_data_mapper.ChecklistDataMapper(self.yaml)

    def init_args(self):
        self.arg_parser.add_argument(
            '-V',
            '--version',
            help="Display the program's version information and exit.",
            action='version',
            version=f'%(prog)s: v{__version__} by {__author__}',
        )

        self.arg_parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Optional: Also log debug messages on console.',
        )

        self.arg_parser.add_argument(
            'report_file',
            help=(
                'Path to the report file to export. A directory exports every checklist '
                'file inside it. May be given more than once.'
            ),
            nargs='+',
            type=pathlib.Path,
        )

        self.arg_parser.add_argument(
            '--format',
            choices=sorted(export.FORMATS),
            help=(
                'Output format. May be omitted if it can be inferred from the extension '
                'of the `--output` file.'
            ),
        )

        self.arg_parser.add_argument(
            '--no-metadata',
            action='store_true',
            help=(
                'Do not include the generator and version metadata of ChecklistFabrik in '
                'the exported document.'
            ),
        )

        self.arg_parser.add_argument(
            '--output',
            help=(
                'Path of the exported document. Only valid when exporting a single report '
                f'file. Use "{STDOUT_TARGET}" to write to stdout. '
                'If omitted, the document is written next to the report file.'
            ),
        )

        self.arg_parser.add_argument(
            '--output-dir',
            help=(
                'Directory the exported documents are written to. The directory is created '
                'if it does not exist. If omitted, each document is written next to its '
                'report file.'
            ),
            type=pathlib.Path,
        )

        self.arg_parser.add_argument(
            '--template',
            action='store_true',
            help=(
                'Treat the input as a checklist template instead of a report, so that Jinja '
                'expressions in default values are rendered.'
            ),
        )

    def init_logging(
        self, console_log_level=logging.INFO, file_log_level=logging.DEBUG, **kwargs
    ):
        # Exported documents can go to stdout, so log messages must not.
        kwargs['console_stream'] = sys.stderr

        super().init_logging(console_log_level, file_log_level, **kwargs)

    def validate_args(self):
        self.sources = self.collect_sources()

        if not self.sources:
            self.arg_parser.error('no checklist files to export')

        if self.args.output is not None:
            if self.args.output_dir is not None:
                self.arg_parser.error(
                    '--output and --output-dir are mutually exclusive'
                )

            if len(self.sources) > 1:
                self.arg_parser.error(
                    '--output may only be used when exporting a single file'
                )

        self.output_format = self.args.format

        if self.output_format is None:
            if self.args.output is None or self.args.output == STDOUT_TARGET:
                self.arg_parser.error(
                    '--format is required unless it can be inferred from --output'
                )

            self.output_format = export.format_from_suffix(self.args.output)

            if self.output_format is None:
                self.arg_parser.error(
                    f'cannot infer the output format from "{self.args.output}". '
                    'Use --format to select one'
                )

    def collect_sources(self):
        """Expand the given paths into the list of checklist files to export."""

        sources = []

        for path in self.args.report_file:
            if path.is_dir():
                found = [
                    match
                    for match in sorted(
                        {
                            match
                            for pattern in REPORT_SUFFIXES
                            for match in path.glob(pattern)
                        }
                    )
                    if self.is_checklist(match)
                ]

                if not found:
                    logger.warning('No checklist files found in directory "%s"', path)

                sources += found
            elif path.is_file():
                sources.append(path)
            else:
                self.arg_parser.error(f'"{path}" is neither a file nor a directory')

        # The same file may be reachable through several arguments; export it only once.
        return sorted(set(sources))

    def is_checklist(self, path):
        """Report whether a file holds a checklist rather than something else.

        A directory of checklists usually also contains files that only hold a page or task
        list for an import. Those are skipped. A file that cannot be parsed at all is kept,
        so the export reports it as a failure instead of quietly leaving it out.
        """

        try:
            data = self.parsed[path] = self.data_mapper.load_yaml(path)
        except checklist_data_mapper.ChecklistLoadError:
            self.unparsable.add(path)
            return True

        if isinstance(data, dict) and 'pages' in data and 'title' in data:
            return True

        logger.info('Skipping "%s" as it does not contain a checklist', path)

        return False

    def run(self):
        if self.args.output_dir is not None:
            try:
                self.args.output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                logger.critical(
                    'Cannot create output directory "%s": %s',
                    self.args.output_dir,
                    error,
                )
                return 1

        failed = 0

        for source in self.sources:
            try:
                self.export_source(source)
            except export.ExportError as error:
                logger.error('Failed to export "%s": %s', source, error)
                failed += 1

        if failed:
            logger.critical(
                '%d of %d files failed to export', failed, len(self.sources)
            )
            return 1

        return 0

    def export_source(self, source):
        """Export a single checklist file."""

        logger.info(
            'Exporting "%s" as %s', source, export.FORMATS[self.output_format]['label']
        )

        checklist = self.load_checklist(source)
        data = export.export_checklist(
            checklist,
            self.output_format,
            include_metadata=not self.args.no_metadata,
            source=source.name,
        )

        if self.args.output == STDOUT_TARGET:
            self.write_stdout(data)
            return

        target = (
            pathlib.Path(self.args.output)
            if self.args.output is not None
            else export.output_path(
                source, self.output_format, output_dir=self.args.output_dir
            )
        )

        if target.resolve() in {candidate.resolve() for candidate in self.sources}:
            raise export.ExportError(
                f'refusing to overwrite the checklist file "{target}" with its own export'
            )

        export.write(target, data, self.output_format)

        logger.info('Wrote "%s"', target)

    def load_checklist(self, source):
        """Load a checklist file without terminating the process if it is broken."""

        if source in self.unparsable:
            raise export.ExportError('cannot parse the file, see the messages above')

        try:
            data = (
                self.parsed[source]
                if source in self.parsed
                else self.data_mapper.load_yaml(source)
            )

            return self.data_mapper.process_checklist(
                data,
                source.parent,
                is_template=self.args.template,
            )
        except (ValueError, checklist_data_mapper.ChecklistLoadError) as error:
            raise export.ExportError(
                f'cannot load checklist ({error or "see the messages above"})'
            ) from error

    def write_stdout(self, data):
        if export.FORMATS[self.output_format]['binary']:
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data)


def main(args=None):
    ExportCli.main(args)
