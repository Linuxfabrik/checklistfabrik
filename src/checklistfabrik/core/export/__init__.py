"""Static export of ChecklistFabrik checklists into human-readable documents.

A checklist is loaded into the regular data model and then turned into a neutral document
(see `document.py`), which one renderer per output format translates into its target
markup. The YAML file itself is never modified: exporting is a read-only operation.
"""

import importlib
import pathlib

from .document import build_document

#: Supported output formats. `suffixes` lists the file extensions that select the format
#: when it is inferred from an output path, `suffix` is the extension used for generated
#: file names.
FORMATS = {
    'asciidoc': {
        'binary': False,
        'label': 'AsciiDoc',
        'mimetype': 'text/plain; charset=utf-8',
        'suffix': '.adoc',
        'suffixes': ('.adoc', '.asciidoc'),
    },
    'html': {
        'binary': False,
        'label': 'HTML',
        'mimetype': 'text/html; charset=utf-8',
        'suffix': '.html',
        'suffixes': ('.htm', '.html'),
    },
    'markdown': {
        'binary': False,
        'label': 'Markdown',
        'mimetype': 'text/markdown; charset=utf-8',
        'suffix': '.md',
        'suffixes': ('.markdown', '.md'),
    },
    'pdf': {
        'binary': True,
        'label': 'PDF',
        'mimetype': 'application/pdf',
        'suffix': '.pdf',
        'suffixes': ('.pdf',),
    },
    'rst': {
        'binary': False,
        'label': 'reStructuredText',
        'mimetype': 'text/x-rst; charset=utf-8',
        'suffix': '.rst',
        'suffixes': ('.rest', '.rst'),
    },
}


class ExportError(Exception):
    """Failure while exporting a checklist."""

    pass


def export_checklist(checklist, output_format, source=None, include_metadata=True):
    """Export a loaded checklist in the requested format."""

    return render(
        build_document(checklist, source=source, include_metadata=include_metadata),
        output_format,
    )


def format_from_suffix(path):
    """Infer the output format from a file extension. Returns None if it is unknown."""

    suffix = pathlib.Path(path).suffix.lower()

    for name, spec in FORMATS.items():
        if suffix in spec['suffixes']:
            return name

    return None


def output_path(source_path, output_format, output_dir=None):
    """Build the output file path for a source file, keeping its name but changing the extension."""

    source_path = pathlib.Path(source_path)
    target = source_path.with_suffix(FORMATS[output_format]['suffix'])

    if output_dir is not None:
        target = pathlib.Path(output_dir) / target.name

    return target


def render(document, output_format):
    """Render a neutral document into the requested format.

    Returns a string for text formats and bytes for binary formats such as PDF.
    """

    if output_format not in FORMATS:
        raise ExportError(f'Unknown output format "{output_format}"')

    renderer = importlib.import_module(f'{__name__}.renderers.{output_format}')

    return renderer.render(document)


def write(path, data, output_format):
    """Write rendered export data to a file, in text or binary mode as the format requires."""

    path = pathlib.Path(path)

    try:
        if FORMATS[output_format]['binary']:
            path.write_bytes(data)
        else:
            path.write_text(data, encoding='utf-8')
    except OSError as error:
        raise ExportError(f'Cannot write "{path}": {error}') from error
