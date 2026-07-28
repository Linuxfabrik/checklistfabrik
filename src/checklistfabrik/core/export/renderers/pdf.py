"""Render an export document as a PDF file.

PDF support is optional because it needs the `fpdf2` package:

    pip install 'checklistfabrik[pdf]'

The built-in PDF fonts cover the Latin-1 character set. Characters outside it are
transliterated where an obvious replacement exists and replaced by `?` otherwise.
"""

import logging
import re

from .. import ExportError, markup
from . import (
    NO_LABEL,
    NOT_ANSWERED,
    NOT_APPLICABLE_PAGE,
    NOT_APPLICABLE_TASK,
    REQUIRED,
    is_verbatim,
    marker,
    progress_text,
    verbatim,
)

FONT = 'Helvetica'
FONT_MONOSPACE = 'Courier'

#: Font sizes in points.
SIZE_BODY = 10
SIZE_CONTENT_HEADING = 11
SIZE_MONOSPACE = 8
SIZE_PAGE_TITLE = 14
SIZE_SMALL = 8
SIZE_TITLE = 18

#: Line height and indentation in millimetres.
INDENT = 5
LINE_HEIGHT = 5

#: Colours, matching the shading and the accent of the interactive interface.
COLOUR_RULE = (188, 195, 206)
COLOUR_SHADE = (247, 248, 249)
COLOUR_SUBTLE = 120

#: Characters that the built-in PDF fonts do not know but that have an obvious replacement.
#: Written as escape sequences because the literal characters are easy to confuse with
#: their replacements.
TRANSLITERATIONS = {
    '\u2010': '-',  # hyphen
    '\u2011': '-',  # non-breaking hyphen
    '\u2013': '-',  # en dash
    '\u2014': '-',  # em dash
    '\u2018': "'",  # left single quotation mark
    '\u2019': "'",  # right single quotation mark
    '\u201c': '"',  # left double quotation mark
    '\u201d': '"',  # right double quotation mark
    '\u2022': '-',  # bullet
    '\u2026': '...',  # horizontal ellipsis
    '\u2192': '->',  # rightwards arrow
}

logger = logging.getLogger(__name__)


#: Marker pairs that fpdf2 interprets, together with any backslashes in front of them.
#: A literal occurrence in a report, such as the command line option `--verbose`, would
#: otherwise underline the rest of the paragraph.
_FPDF_MARKER = re.compile(r'(\\*)(\*\*|__|~~|--)')


class InlineWriter(markup.MarkupWriter):
    """Render inline Markdown in the dialect that fpdf2 understands.

    fpdf2 applies a small Markdown subset itself when a cell is written with
    `markdown=True`. Emphasis is therefore handed over to fpdf2 instead of being dropped,
    while everything it cannot show, such as an inline code span, falls back to plain text.
    """

    def escape(self, text):
        # fpdf2 reads a marker literally when an odd number of backslashes precedes it.
        # Existing backslashes are doubled so that the added one always wins.
        escaped = _FPDF_MARKER.sub(lambda match: f'{match.group(1) * 2}\\{match.group(2)}', text)

        # An unescaped bracket could start a link.
        return escaped.replace('[', '\\[')

    def codespan(self, text):
        # No inline font switching exists, so a code span keeps its text only.
        return self.escape(text)

    def strong(self, text):
        return f'**{text}**' if text else ''

    def emphasis(self, text):
        return f'__{text}__' if text else ''

    def strikethrough(self, text):
        return f'~~{text}~~' if text else ''

    def link(self, text, url):
        # fpdf2 turns this into a real, clickable link.
        return f'[{text}]({url})' if text else f'[{url}]({url})'

    def image(self, alt, url):
        return self.link(alt, url)


def plain_inline(nodes):
    """Render inline nodes as plain text.

    A label is written in a bold font. Handing its emphasis to fpdf2 as well would toggle
    that bold off again, so the markup is dropped instead.
    """

    return markup.TextWriter().render_inline(nodes)


def render(document):
    """Render the document and return it as PDF bytes."""

    fpdf = _import_fpdf()
    writer = InlineWriter()

    pdf = _create_pdf(fpdf, document)
    pdf.add_page()

    _title(pdf, document)
    _metadata(pdf, document)

    if document['description']:
        _paragraph(pdf, document['description'])

    for page in document['pages']:
        _page(pdf, page, writer)

    return bytes(pdf.output())


def _import_fpdf():
    try:
        import fpdf
    except ImportError as error:
        raise ExportError(
            'PDF export requires the "fpdf2" package. '
            "Install it with: pip install 'checklistfabrik[pdf]'"
        ) from error

    return fpdf


def _create_pdf(fpdf, document):
    footer_text = _text(document['source'] or document['title'])

    class ChecklistPdf(fpdf.FPDF):
        """A PDF that repeats the report name and the page number in its footer."""

        def footer(self):
            self.set_y(-15)
            self.set_font(FONT, 'I', SIZE_SMALL)
            self.set_text_color(120)
            self.cell(self.epw / 2, LINE_HEIGHT, footer_text)
            self.cell(self.epw / 2, LINE_HEIGHT, str(self.page_no()), align='R')
            self.set_text_color(0)

    pdf = ChecklistPdf()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_creator('ChecklistFabrik')
    pdf.set_title(_text(document['title']))

    return pdf


def _text(text):
    """Fit a string into the character set of the built-in PDF fonts."""

    for character, replacement in TRANSLITERATIONS.items():
        text = text.replace(character, replacement)

    encoded = text.encode('latin-1', errors='replace')

    if b'?' in encoded and '?' not in text:
        logger.warning('PDF export replaced characters that the built-in fonts cannot display')

    return encoded.decode('latin-1')


def _required(text, required):
    return f'{text} ({REQUIRED})' if required else text


def _write(pdf, text, style='', size=SIZE_BODY, font=FONT, indent=0, markdown=False, fill=False):
    """Write a block of text, wrapping it and starting a new page where needed.

    `markdown` hands the emphasis markers of `InlineWriter` over to fpdf2. It must stay off
    for values that come out of a report, so that a value can never restyle the document.
    """

    left_margin = pdf.l_margin

    pdf.set_font(font, style, size)
    pdf.set_left_margin(left_margin + indent)
    pdf.set_x(left_margin + indent)
    pdf.multi_cell(
        0,
        LINE_HEIGHT,
        _text(text),
        # Left-aligned, not justified: justification stretches the word gaps of a wrapped
        # line and makes a checklist hard to scan.
        align='L',
        fill=fill,
        markdown=markdown,
        new_x='LMARGIN',
        new_y='NEXT',
    )
    pdf.set_left_margin(left_margin)
    pdf.set_x(left_margin)


def _write_marked(pdf, item_marker, text, indent=0, style=''):
    """Write a marker followed by text whose wrapped lines line up under that text."""

    left_margin = pdf.l_margin

    pdf.set_font(FONT, style, SIZE_BODY)
    width = pdf.get_string_width(f'{item_marker} ')

    pdf.set_left_margin(left_margin + indent)
    pdf.set_x(left_margin + indent)
    pdf.cell(width, LINE_HEIGHT, _text(item_marker))

    pdf.set_left_margin(left_margin + indent + width)
    pdf.multi_cell(
        0,
        LINE_HEIGHT,
        _text(text),
        align='L',
        markdown=True,
        new_x='LMARGIN',
        new_y='NEXT',
    )

    pdf.set_left_margin(left_margin)
    pdf.set_x(left_margin)


def _spacer(pdf, height=2):
    pdf.ln(height)


def _code(pdf, code, indent=0):
    """Write a verbatim block in a fixed-width font on a shaded background."""

    pdf.set_fill_color(*COLOUR_SHADE)
    _write(
        pdf,
        code,
        fill=True,
        font=FONT_MONOSPACE,
        indent=indent,
        size=SIZE_MONOSPACE,
    )
    pdf.set_fill_color(255, 255, 255)


def _rule(pdf, indent=0):
    pdf.set_draw_color(*COLOUR_RULE)
    pdf.line(pdf.l_margin + indent, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_draw_color(0, 0, 0)
    _spacer(pdf, 3)


def _title(pdf, document):
    _write(pdf, document['title'] or 'Checklist', style='B', size=SIZE_TITLE)
    _spacer(pdf)


def _metadata(pdf, document):
    fields = []

    if document['generator']:
        fields.append(('Generator', document['generator']))

    fields.append(('Progress', progress_text(document['stats'])))

    if document['source']:
        fields.append(('Source', document['source']))

    if document['version']:
        fields.append(('Version', document['version']))

    for name, value in fields:
        pdf.set_font(FONT, 'B', SIZE_SMALL)
        pdf.cell(25, LINE_HEIGHT, _text(f'{name}:'))
        pdf.set_font(FONT, '', SIZE_SMALL)
        pdf.multi_cell(0, LINE_HEIGHT, _text(value), new_x='LMARGIN', new_y='NEXT')

    _spacer(pdf, 4)


def _paragraph(pdf, text, indent=0):
    _write(pdf, text, indent=indent)
    _spacer(pdf)


def _page(pdf, page, writer):
    _spacer(pdf, 6)
    _write(pdf, page['title'] or 'Page', style='B', size=SIZE_PAGE_TITLE)
    _spacer(pdf)

    if not page['applicable']:
        _write(pdf, NOT_APPLICABLE_PAGE, style='I')
        _spacer(pdf)

    for task in page['tasks']:
        _task(pdf, task, writer)


def _task(pdf, task, writer):
    if not task['applicable']:
        _write(pdf, NOT_APPLICABLE_TASK, style='I')

    for block in task['blocks']:
        _block(pdf, block, writer)


def _block(pdf, block, writer):
    block_type = block['type']

    if block_type == 'checklist':
        _checklist(pdf, block, writer)
    elif block_type == 'field':
        _field(pdf, block, writer)
    elif block_type == 'html':
        # Markup cannot be reproduced in a PDF, so only the text content is kept.
        _paragraph(pdf, markup.strip_tags(block['content']))
    elif block_type == 'markdown':
        _markdown(pdf, block['content'], writer)
    elif block_type == 'note':
        _write(pdf, block['content'], style='I')
        _spacer(pdf)
    elif block_type == 'reference':
        _reference(pdf, block, writer)


def _markdown(pdf, content, writer, indent=0):
    """Lay out a block of Markdown, keeping its structure instead of flattening it."""

    for node in markup.parse(content):
        _markdown_node(pdf, node, writer, indent)


def _markdown_node(pdf, node, writer, indent):
    node_type = node['type']
    attrs = node.get('attrs') or {}

    if node_type == 'blank_line':
        return

    if node_type in ('paragraph', 'block_text'):
        _write(pdf, writer.render_inline(node.get('children')), indent=indent, markdown=True)
        _spacer(pdf)
    elif node_type == 'heading':
        _write(
            pdf,
            writer.render_inline(node.get('children')),
            indent=indent,
            markdown=True,
            size=SIZE_CONTENT_HEADING,
            style='B',
        )
        _spacer(pdf)
    elif node_type == 'block_code':
        _code(pdf, node.get('raw', '').rstrip('\n'), indent=indent + INDENT)
        _spacer(pdf)
    elif node_type == 'block_quote':
        # A PDF has no quote marker, so the indentation and the italics carry the meaning.
        pdf.set_text_color(COLOUR_SUBTLE)
        for child in node.get('children') or []:
            _markdown_node(pdf, child, writer, indent + INDENT)
        pdf.set_text_color(0)
    elif node_type == 'list':
        _list(pdf, node, writer, indent, ordered=attrs.get('ordered', False))
        _spacer(pdf)
    elif node_type == 'table':
        _table(pdf, node, writer, indent)
    elif node_type == 'thematic_break':
        _rule(pdf, indent)
    elif node_type == 'block_html':
        _paragraph(pdf, markup.strip_tags(node.get('raw', '')), indent=indent)
    elif node.get('children'):
        for child in node['children']:
            _markdown_node(pdf, child, writer, indent)


def _list(pdf, node, writer, indent, ordered):
    for number, item in enumerate(node.get('children') or [], start=1):
        bullet = f'{number}.' if ordered else '-'

        for position, child in enumerate(item.get('children') or []):
            if child['type'] == 'list':
                _list(
                    pdf,
                    child,
                    writer,
                    indent + INDENT,
                    ordered=(child.get('attrs') or {}).get('ordered', False),
                )
            elif position == 0:
                # The bullet belongs to the first block of the item, the rest is indented
                # underneath it.
                _write(
                    pdf,
                    f'{bullet} {writer.render_inline(child.get("children"))}',
                    indent=indent,
                    markdown=True,
                )
            else:
                _markdown_node(pdf, child, writer, indent + INDENT)


def _table(pdf, node, writer, indent):
    head = []
    rows = []

    # A table cell is written by fpdf2 itself, which does not apply the Markdown subset
    # there, so the cell texts are reduced to plain text.
    cell_writer = markup.TextWriter()

    for section in node.get('children') or []:
        if section['type'] == 'table_head':
            # Mistune stores the header cells directly under `table_head`.
            head = [
                cell_writer.render_inline(cell.get('children'))
                for cell in section.get('children') or []
            ]
        elif section['type'] == 'table_body':
            rows = [
                [
                    cell_writer.render_inline(cell.get('children'))
                    for cell in row.get('children') or []
                ]
                for row in section.get('children') or []
            ]

    left_margin = pdf.l_margin

    pdf.set_font(FONT, '', SIZE_BODY)
    pdf.set_left_margin(left_margin + indent)

    with pdf.table(first_row_as_headings=bool(head), line_height=LINE_HEIGHT) as table:
        for values in ([head] if head else []) + rows:
            row = table.row()

            for value in values:
                row.cell(_text(value))

    pdf.set_left_margin(left_margin)
    _spacer(pdf)


def _checklist(pdf, block, writer):
    _label(pdf, block['label'], block['required'], writer)

    for item in block['items']:
        _item(pdf, item['label'], marker(item['checked']), item['required'], writer)

    _spacer(pdf)


def _item(pdf, label, item_marker, required, writer, extra=()):
    """Lay out one check item: marker plus label, with any further blocks below it."""

    lead, rest = markup.split_lead_paragraph(label)
    head = writer.render_inline(lead['children']) if lead is not None else ''

    if required:
        head = f'{head} ({REQUIRED})' if head else f'({REQUIRED})'

    if head:
        _write_marked(pdf, item_marker, head)
    elif rest:
        # The label starts with a block of its own, so the marker gets a line for itself.
        _write(pdf, item_marker)
    else:
        _write_marked(pdf, item_marker, NO_LABEL)

    for node in rest:
        _markdown_node(pdf, node, writer, INDENT)

    for block in extra:
        block(pdf)


def _label(pdf, label, required, writer):
    """Write a task label: its first sentence in bold, any further blocks below it."""

    lead, rest = markup.split_lead_paragraph(label)

    if lead is not None:
        _write(pdf, _required(plain_inline(lead['children']), required), style='B')

    for node in rest:
        _markdown_node(pdf, node, writer, 0)


def _field(pdf, block, writer):
    _label(pdf, block['label'], block['required'], writer)

    values = block['values']

    if not values:
        _write(pdf, NOT_ANSWERED, style='I', indent=INDENT)
    elif is_verbatim(block):
        # Keep line breaks and alignment of pasted command output intact.
        _code(pdf, verbatim(values), indent=INDENT)
    else:
        for value in values:
            _write(pdf, value, indent=INDENT)

    _spacer(pdf)


def _reference(pdf, block, writer):
    def path(target):
        _write(target, f'Checklist: {block["path"]}', size=SIZE_SMALL, indent=INDENT)

    def description(target):
        _markdown(target, block['description'], writer, indent=INDENT)

    extra = [description, path] if block['description'] else [path]

    _item(pdf, block['label'], marker(block['checked']), block['required'], writer, extra=extra)
    _spacer(pdf)
