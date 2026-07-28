"""Building blocks for the static export representation of a task.

A task module renders HTML through its `main()` function. To also appear in a static
export it implements `export()`, which returns a dictionary with a `blocks` key holding a
list of the neutral blocks defined here. The exporters walk those blocks and translate
them into the target markup, so a task module never has to know anything about
reStructuredText, AsciiDoc, Markdown, HTML or PDF.

Labels are Markdown source with the Jinja expressions already resolved; escaping and the
conversion into the target markup happen in the exporters. Captured values are plain text
and are never interpreted as markup, so a value such as `*` cannot alter the layout of an
exported document. Use `plain_text()` to feed a Markdown-formatted label into a value.
"""

from . import markup


def checklist(items, label=None, required=False):
    """A group of check items, each of which is either checked or unchecked."""

    return {
        'items': list(items),
        'label': label or '',
        'required': bool(required),
        'type': 'checklist',
    }


def checklist_item(label, checked, required=False):
    """A single entry of a `checklist` block."""

    return {
        'checked': bool(checked),
        'label': label or '',
        'required': bool(required),
    }


def field(label, values, required=False, monospace=False):
    """A captured value. An empty `values` list marks the field as unanswered."""

    return {
        'label': label or '',
        'monospace': bool(monospace),
        'required': bool(required),
        'type': 'field',
        'values': list(values),
    }


def html(content):
    """Raw HTML. Only the HTML export can reproduce it verbatim."""

    return {
        'content': content or '',
        'type': 'html',
    }


def markdown(content):
    """A block of Markdown source, converted into the target markup by the exporter."""

    return {
        'content': content or '',
        'type': 'markdown',
    }


def note(content, level='info'):
    """An exporter-generated remark, for example about a skipped or unsupported task."""

    return {
        'content': content or '',
        'level': level,
        'type': 'note',
    }


def reference(label, path, checked=False, description='', required=False):
    """A reference to another checklist, together with its confirmation state."""

    return {
        'checked': bool(checked),
        'description': description or '',
        'label': label or '',
        'path': path or '',
        'required': bool(required),
        'type': 'reference',
    }


def plain_text(text):
    """Strip the Markdown markup from a label so it can be used as a plain-text value."""

    return markup.TextWriter().render(text)


def values_of(value):
    """Normalise a fact value into a list of non-empty strings."""

    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item is not None and str(item) != '']

    if str(value) == '':
        return []

    return [str(value)]
