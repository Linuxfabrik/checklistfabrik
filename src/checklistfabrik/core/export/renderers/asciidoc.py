"""Render an export document as AsciiDoc."""

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


def render(document):
    """Render the document and return it as AsciiDoc source."""

    writer = markup.AsciiDocWriter()

    parts = [f'= {_single_line(writer.escape(document["title"])) or "Checklist"}']
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
    return mark_first_line(text, f' _({REQUIRED})_') if required else text


def _metadata(document, writer):
    # The terms of the description list are generated, so they can never contain the `::`
    # separator that would break the list.
    fields = []

    if document['generator']:
        fields.append(('Generator', writer.escape(document['generator'])))

    fields.append(('Progress', writer.escape(progress_text(document['stats']))))

    if document['source']:
        fields.append(('Source', f'`+{document["source"]}+`'))

    if document['version']:
        fields.append(('Version', writer.escape(document['version'])))

    return ['[horizontal]\n' + '\n'.join(f'{name}:: {value}' for name, value in fields)]


def _page(page, writer):
    parts = [f'== {_single_line(writer.escape(page["title"])) or "Page"}']

    if not page['applicable']:
        parts.append(_admonition('NOTE', NOT_APPLICABLE_PAGE))

    for task in page['tasks']:
        parts += _task(task, writer)

    return parts


def _task(task, writer):
    parts = []

    if not task['applicable']:
        parts.append(f'_{NOT_APPLICABLE_TASK}_')

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
    items = '\n'.join(
        _item(writer, item['label'], marker(item['checked']), item['required'])
        for item in block['items']
    )

    label = writer.render(block['label'])

    if not label:
        return items

    return f'{_emphasise(label, block["required"])}\n\n{items}'


def _item(writer, label, item_marker, required, extra=()):
    """Lay out one check item: marker plus label, with any further blocks below it.

    AsciiDoc attaches a block to the item above it with a `+` on a line of its own.
    Indentation must not be used, as it would turn the block into a literal one.
    """

    lead, rest = markup.split_lead_paragraph(label)
    head = writer.render_inline(lead['children']) if lead is not None else ''

    if required:
        head = _required(head, True) if head else f'_({REQUIRED})_'

    blocks = [block for block in [writer.render_nodes(rest), *extra] if block]

    if not head and not blocks:
        head = NO_LABEL

    attached = ''.join(f'\n+\n{block}' for block in blocks)

    return f'* {item_marker} {head}{attached}' if head else f'* {item_marker}{attached}'


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
        return f'_{NOT_ANSWERED}_'

    if is_verbatim(block):
        # Keep line breaks and alignment of pasted command output intact.
        return f'----\n{verbatim(values)}\n----'

    if len(values) == 1:
        return writer.escape(values[0])

    return '\n'.join(f'* {writer.escape(value)}' for value in values)


def _answer(block, writer):
    value = _value(block, writer)
    separator = '\n\n' if '\n' in value else ' '

    return f'**{ANSWER}:**{separator}{value}'


def _html(block):
    content = block['content'].strip()

    if not content:
        return ''

    return f'++++\n{content}\n++++'


def _note(block, writer):
    style = 'WARNING' if block['level'] in ('error', 'warning') else 'NOTE'

    return _admonition(style, writer.escape(block['content']))


def _admonition(style, content):
    return f'[{style}]\n====\n{content}\n===='


def _reference(block, writer):
    extra = []

    if block['description']:
        extra.append(writer.render(block['description']))

    extra.append(f'Checklist: `+{block["path"]}+`')

    return _item(
        writer, block['label'], marker(block['checked']), block['required'], extra=extra
    )
