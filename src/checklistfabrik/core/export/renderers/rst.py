"""Render an export document as reStructuredText."""

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

#: Indentation of a definition, a directive body and a literal block.
INDENT = '   '

#: Bullet of a check item. Its width is also the indentation of the blocks below the item.
BULLET = '- '


def render(document):
    """Render the document and return it as reStructuredText source."""

    writer = markup.RstWriter()

    parts = [_title(document, writer), _metadata(document, writer)]

    if document['description']:
        parts.append(writer.escape(document['description']))

    for page in document['pages']:
        parts += _page(page, writer)

    return '\n\n'.join(part for part in parts if part) + '\n'


def _required(text, required):
    return mark_first_line(text, f' *({REQUIRED})*') if required else text


def _title(document, writer):
    title = writer.escape(document['title']).strip() or 'Checklist'
    rule = '=' * len(title)

    # An overlined title is a section level of its own, so the pages below can reuse `=`.
    return f'{rule}\n{title}\n{rule}'


def _metadata(document, writer):
    fields = []

    if document['generator']:
        fields.append(('Generator', writer.escape(document['generator'])))

    fields.append(('Progress', writer.escape(progress_text(document['stats']))))

    if document['source']:
        fields.append(('Source', f'``{document["source"]}``'))

    if document['version']:
        fields.append(('Version', writer.escape(document['version'])))

    return '\n'.join(f':{name}: {value}' for name, value in fields)


def _page(page, writer):
    title = writer.escape(page['title']).strip() or 'Page'
    parts = [f'{title}\n{"=" * len(title)}']

    if not page['applicable']:
        parts.append(_directive('note', NOT_APPLICABLE_PAGE))

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
        return _html(block)

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

    return f'{_required(label, block["required"])}\n\n{items}'


def _item(writer, label, item_marker, required, extra=()):
    """Lay out one check item: marker plus label, with any further blocks below it."""

    lead, rest = markup.split_lead_paragraph(label)
    head = writer.render_inline(lead['children']) if lead is not None else ''

    if required:
        head = f'{head} *({REQUIRED})*' if head else f'*({REQUIRED})*'

    blocks = [
        block for block in [head, writer.render_nodes(rest), *extra] if block
    ] or [NO_LABEL]
    body = '\n\n'.join(blocks)

    # The bullet is `- `, so everything below the first line lines up two columns in.
    continuation = ' ' * len(BULLET)

    if head:
        return markup.indent_lines(body, continuation, f'{BULLET}{item_marker} ')

    # The label starts with a block of its own, so the marker gets a line for itself.
    return f'{BULLET}{item_marker}\n\n{markup.indent_lines(body, continuation)}'


def _field(block, writer):
    label = writer.render(block['label'])

    if not label:
        return _value(block, writer)

    label = _required(label, block['required'])

    if '\n' not in label:
        # A single-line label becomes the term of a definition list.
        return f'{label}\n{markup.indent_lines(_value(block, writer), INDENT)}'

    # A label spanning several blocks is content of its own, so the value follows below it.
    return f'{label}\n\n{_answer(block, writer)}'


def _value(block, writer):
    values = block['values']

    if not values:
        return f'*{NOT_ANSWERED}*'

    if is_verbatim(block):
        # Keep line breaks and alignment of pasted command output intact.
        return '::\n\n' + markup.indent_lines(verbatim(values), INDENT)

    if len(values) == 1:
        return writer.escape(values[0])

    return '\n'.join(f'- {writer.escape(value)}' for value in values)


def _answer(block, writer):
    if block['values'] and is_verbatim(block):
        # `Answer::` introduces the literal block that follows it.
        return f'{ANSWER}::\n\n{markup.indent_lines(verbatim(block["values"]), INDENT)}'

    value = _value(block, writer)

    if '\n' in value:
        return f'{ANSWER}:\n\n{value}'

    return f'{ANSWER}: {value}'


def _html(block):
    content = block['content'].strip()

    if not content:
        return ''

    return f'.. raw:: html\n\n{markup.indent_lines(content, INDENT)}'


def _note(block, writer):
    # `note` and `warning` are the two admonitions every reStructuredText toolchain knows.
    directive = 'warning' if block['level'] in ('error', 'warning') else 'note'

    return _directive(directive, writer.escape(block['content']))


def _reference(block, writer):
    extra = []

    if block['description']:
        extra.append(writer.render(block['description']))

    extra.append(f'Checklist: ``{block["path"]}``')

    return _item(
        writer, block['label'], marker(block['checked']), block['required'], extra=extra
    )


def _directive(name, content):
    return f'.. {name}::\n\n{markup.indent_lines(content, INDENT)}'
