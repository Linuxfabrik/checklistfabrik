"""Render an export document as Markdown."""

from .. import markup
from . import (
    ANSWER,
    NO_LABEL,
    NOT_ANSWERED,
    NOT_APPLICABLE_PAGE,
    NOT_APPLICABLE_TASK,
    REQUIRED,
    is_verbatim,
    mark_first_line,
    marker,
    progress_text,
    verbatim,
)

#: Indentation that keeps a follow-up block inside its list item. It matches the width of
#: the `- ` bullet: indenting further would turn a paragraph into an indented code block.
INDENT = '  '


def render(document):
    """Render the document and return it as Markdown source."""

    writer = markup.MarkdownWriter()

    parts = [f'# {_single_line(writer.escape(document["title"])) or "Checklist"}']
    parts += _metadata(document, writer)

    if document['description']:
        parts.append(writer.escape(document['description']))

    for page in document['pages']:
        parts += _page(page, writer)

    return '\n\n'.join(part for part in parts if part) + '\n'


def _single_line(text):
    """Collapse a title into one line, as a heading cannot span several."""

    return ' '.join(text.split())


def _required(text, required):
    return mark_first_line(text, f' *({REQUIRED})*') if required else text


def _metadata(document, writer):
    fields = []

    if document['generator']:
        fields.append(('Generator', writer.escape(document['generator'])))

    fields.append(('Progress', writer.escape(progress_text(document['stats']))))

    if document['source']:
        fields.append(('Source', f'`{document["source"]}`'))

    if document['version']:
        fields.append(('Version', writer.escape(document['version'])))

    return ['\n'.join(f'- **{name}:** {value}' for name, value in fields)]


def _page(page, writer):
    parts = [f'## {_single_line(writer.escape(page["title"])) or "Page"}']

    if not page['applicable']:
        parts.append(_quote(f'**Note:** {NOT_APPLICABLE_PAGE}'))

    for task in page['tasks']:
        parts += _task(task, writer)

    return parts


def _task(task, writer):
    parts = []

    if not task['applicable']:
        parts.append(f'*{NOT_APPLICABLE_TASK}*')

    for block in task['blocks']:
        rendered = _block(block, writer)

        if rendered:
            parts.append(rendered)

    return parts


def _block(block, writer):
    block_type = block['type']

    if block_type == 'checklist':
        return _checklist(block, writer)

    if block_type == 'field':
        return _field(block, writer)

    if block_type == 'html':
        # Markdown passes raw HTML through to the renderer of the hosting platform.
        return block['content'].strip()

    if block_type == 'markdown':
        return writer.render(block['content'])

    if block_type == 'note':
        return _note(block, writer)

    if block_type == 'reference':
        return _reference(block, writer)

    return ''


def _checklist(block, writer):
    # A blank line between the items keeps the blocks of one item apart from the next.
    items = '\n\n'.join(
        _item(writer, item['label'], marker(item['checked']), item['required'])
        for item in block['items']
    )

    label = writer.render(block['label'])

    if not label:
        return items

    return f'{_emphasise(label, block["required"])}\n\n{items}'


def _item(writer, label, item_marker, required, extra=()):
    """Lay out one check item: marker plus label, with any further blocks below it."""

    lead, rest = markup.split_lead_paragraph(label)
    head = writer.render_inline(lead['children']) if lead is not None else ''

    if required:
        head = _required(head, True) if head else f'*({REQUIRED})*'

    blocks = [
        block for block in [head, writer.render_nodes(rest), *extra] if block
    ] or [NO_LABEL]
    body = '\n\n'.join(blocks)

    if head:
        return markup.indent_lines(body, INDENT, f'- {item_marker} ')

    # The label starts with a block of its own, so the marker gets a line for itself.
    return f'- {item_marker}\n\n{markup.indent_lines(body, INDENT)}'


def _emphasise(label, required):
    """Set a label in bold, keeping any blocks below it as they are."""

    first, newline, rest = label.partition('\n')

    return _required(f'**{first}**{newline}{rest}', required)


def _field(block, writer):
    label = writer.render(block['label'])

    if not label:
        return _value(block, writer)

    if '\n' not in label:
        return f'{_emphasise(label, block["required"])}\n\n{_value(block, writer)}'

    # A label spanning several blocks is content of its own, so the value follows below it.
    return f'{_required(label, block["required"])}\n\n{_answer(block, writer)}'


def _value(block, writer):
    values = block['values']

    if not values:
        return f'*{NOT_ANSWERED}*'

    if is_verbatim(block):
        # Keep line breaks and alignment of pasted command output intact.
        return f'```\n{verbatim(values)}\n```'

    if len(values) == 1:
        return writer.escape(values[0])

    return '\n'.join(f'- {writer.escape(value)}' for value in values)


def _answer(block, writer):
    value = _value(block, writer)
    separator = '\n\n' if '\n' in value else ' '

    return f'**{ANSWER}:**{separator}{value}'


def _note(block, writer):
    prefix = 'Warning' if block['level'] in ('error', 'warning') else 'Note'

    return _quote(f'**{prefix}:** {writer.escape(block["content"])}')


def _quote(text):
    return '\n'.join(f'> {line}'.rstrip() for line in text.split('\n'))


def _reference(block, writer):
    extra = []

    if block['description']:
        extra.append(writer.render(block['description']))

    extra.append(f'Checklist: `{block["path"]}`')

    return _item(
        writer, block['label'], marker(block['checked']), block['required'], extra=extra
    )
