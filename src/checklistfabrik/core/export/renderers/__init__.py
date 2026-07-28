"""Renderers that turn a neutral export document into a concrete document format.

Every renderer exposes a single `render(document)` function. The wording shared by all of
them lives here so an exported report reads the same in every format.
"""

#: A label is Markdown and may consist of several blocks, for example a sentence followed
#: by a code block. Where that happens, the label becomes ordinary document content and the
#: captured value is attached below it under this word.
ANSWER = 'Answer'

CHECKED = '[x]'
NOT_ANSWERED = 'not answered'
NOT_APPLICABLE_PAGE = 'This page was marked as not applicable based on previous input.'
NOT_APPLICABLE_TASK = 'This task was marked as not applicable based on previous input.'
NO_LABEL = 'Unlabelled entry'
REQUIRED = 'required'
UNCHECKED = '[ ]'


def progress_text(stats):
    """Describe the overall completion state in a single sentence."""

    if not stats['total']:
        return 'No completable items'

    return f'{stats["done"]} of {stats["total"]} items completed ({stats["percent"]}%)'


def marker(checked):
    """Return the checkbox marker for a checked or unchecked item."""

    return CHECKED if checked else UNCHECKED


def verbatim(values):
    """Join values for a verbatim block, without the empty lines a block scalar leaves."""

    return '\n'.join(values).strip('\n')


def is_verbatim(block):
    """Report whether a field has to keep its line breaks and alignment."""

    return block['monospace'] or any('\n' in value for value in block['values'])


def mark_first_line(text, suffix):
    """Append a suffix to the first line of a rendered label.

    A label may span several blocks. Appending to the end would put the marker after a code
    block instead of next to the text it belongs to.
    """

    if not suffix:
        return text

    first, newline, rest = text.partition('\n')

    return f'{first}{suffix}{newline}{rest}'
