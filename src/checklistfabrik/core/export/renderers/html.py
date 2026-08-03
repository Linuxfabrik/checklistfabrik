"""Render an export document as a self-contained HTML file.

The stylesheet is embedded and no external resources are referenced, so the result can be
archived, mailed around or opened from a file system without a web server.
"""

import markupsafe

from .. import markup
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

STYLESHEET = """\
:root {
  --clf-accent: #e85600;
  --clf-border: #bcc3ce;
  --clf-header: #546d78;
  --clf-muted: #7b8794;
  --clf-shade: #f7f8f9;
  --clf-text: #3b4351;
}
* { box-sizing: border-box; }
body {
  color: var(--clf-text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  margin: 0;
}
header.clf-header {
  background: var(--clf-header);
  color: #fff;
  padding: 1.5rem 2rem;
}
header.clf-header h1 { font-size: 1.6rem; margin: 0; }
main { margin: 0 auto; max-width: 60rem; padding: 2rem; }
h2 {
  border-bottom: 1px solid var(--clf-border);
  font-size: 1.3rem;
  margin-top: 2.5rem;
  padding-bottom: 0.3rem;
}
dl.clf-metadata { display: grid; grid-template-columns: max-content 1fr; gap: 0.2rem 1rem; margin: 0; }
dl.clf-metadata dt { color: var(--clf-muted); }
dl.clf-metadata dd { margin: 0; }
.clf-task { margin: 1.2rem 0; }
.clf-label { font-weight: 600; }
.clf-required { color: var(--clf-accent); font-weight: 400; }
.clf-value { border-left: 3px solid var(--clf-border); margin: 0.3rem 0; padding-left: 0.8rem; }
.clf-empty { color: var(--clf-muted); font-style: italic; }
.clf-checklist { list-style: none; margin: 0.3rem 0; padding: 0; }
.clf-checklist li { margin: 0.2rem 0; }
.clf-marker { color: var(--clf-accent); font-family: monospace; }
.clf-reference { border-left: 3px solid var(--clf-border); padding-left: 0.8rem; }
.clf-reference-path { color: var(--clf-muted); font-size: 0.9rem; }
.clf-note {
  background: var(--clf-shade);
  border-left: 3px solid var(--clf-header);
  margin: 1rem 0;
  padding: 0.6rem 0.8rem;
}
.clf-note-warning { border-left-color: var(--clf-accent); }
.clf-skipped { color: var(--clf-muted); font-style: italic; }
code, pre { background: var(--clf-shade); font-size: 0.9em; }
code { padding: 0.1rem 0.3rem; }
pre { overflow-x: auto; padding: 0.6rem 0.8rem; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; }
td, th { border: 1px solid var(--clf-border); padding: 0.3rem 0.6rem; text-align: left; }
blockquote {
  border-left: 3px solid var(--clf-border);
  color: var(--clf-muted);
  margin: 1rem 0;
  padding-left: 0.8rem;
}
footer {
  border-top: 1px solid var(--clf-border);
  color: var(--clf-muted);
  font-size: 0.85rem;
  margin: 3rem auto 0;
  max-width: 60rem;
  padding: 1rem 2rem 2rem;
}
footer a { color: inherit; }
"""

DOCUMENT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
{stylesheet}</style>
</head>
<body>
<header class="clf-header">
<h1>{title}</h1>
</header>
<main>
{metadata}
{body}
</main>
<footer>
<p>Exported with <a href="https://github.com/Linuxfabrik/checklistfabrik">ChecklistFabrik</a>
by <a href="https://www.linuxfabrik.ch">Linuxfabrik GmbH</a>, Zurich/Switzerland.</p>
</footer>
</body>
</html>
"""


def render(document):
    """Render the document and return it as a self-contained HTML page."""

    writer = markup.HtmlWriter()

    body = []

    if document['description']:
        body.append(f'<p>{_escape(document["description"])}</p>')

    for page in document['pages']:
        body += _page(page, writer)

    return DOCUMENT_TEMPLATE.format(
        body='\n'.join(body),
        metadata=_metadata(document),
        stylesheet=STYLESHEET,
        title=_escape(document['title']) or 'Checklist',
    )


def _escape(text):
    return str(markupsafe.escape(text))


def _required(html, required):
    return (
        f'{html} <span class="clf-required">({REQUIRED})</span>' if required else html
    )


def _metadata(document):
    fields = []

    if document['generator']:
        fields.append(('Generator', _escape(document['generator'])))

    fields.append(('Progress', _escape(progress_text(document['stats']))))

    if document['source']:
        fields.append(('Source', f'<code>{_escape(document["source"])}</code>'))

    if document['version']:
        fields.append(('Version', _escape(document['version'])))

    items = '\n'.join(f'<dt>{name}</dt><dd>{value}</dd>' for name, value in fields)

    return f'<dl class="clf-metadata">\n{items}\n</dl>'


def _page(page, writer):
    parts = [f'<h2>{_escape(page["title"]) or "Page"}</h2>']

    if not page['applicable']:
        parts.append(_note_html(NOT_APPLICABLE_PAGE, 'info'))

    for task in page['tasks']:
        parts.append(_task(task, writer))

    return parts


def _task(task, writer):
    parts = []

    if not task['applicable']:
        parts.append(f'<p class="clf-skipped">{NOT_APPLICABLE_TASK}</p>')

    for block in task['blocks']:
        rendered = _block(block, writer)

        if rendered:
            parts.append(rendered)

    if not parts:
        return ''

    return '<div class="clf-task">\n{}\n</div>'.format('\n'.join(parts))


def _block(block, writer):
    block_type = block['type']

    if block_type == 'checklist':
        return _checklist(block, writer)

    if block_type == 'field':
        return _field(block, writer)

    if block_type == 'html':
        return block['content']

    if block_type == 'markdown':
        return writer.render(block['content'])

    if block_type == 'note':
        return _note_html(block['content'], block['level'])

    if block_type == 'reference':
        return _reference(block, writer)

    return ''


def _checklist(block, writer):
    items = '\n'.join(
        _item(writer, item['label'], marker(item['checked']), item['required'])
        for item in block['items']
    )

    checklist = f'<ul class="clf-checklist">\n{items}\n</ul>'
    head, rest = markup.split_lead_html(writer.render(block['label']))

    if not head and not rest:
        return checklist

    return '{}\n{}\n{}'.format(
        f'<div class="clf-label">{_required(head, block["required"])}</div>'
        if head
        else '',
        rest,
        checklist,
    ).strip()


def _item(writer, label, item_marker, required, extra=()):
    """Lay out one check item: marker plus label, with any further blocks below it."""

    head, rest = markup.split_lead_html(writer.render(label))

    if not head and not rest:
        head = NO_LABEL

    body = '\n'.join(part for part in [rest, *extra] if part)

    return '<li><span class="clf-marker">{}</span> {}{}</li>'.format(
        item_marker,
        _required(head, required),
        f'\n{body}' if body else '',
    )


def _field(block, writer):
    value = _value(block)
    head, rest = markup.split_lead_html(writer.render(block['label']))

    if not head and not rest:
        return value

    label = (
        f'<div class="clf-label">{_required(head, block["required"])}</div>'
        if head
        else ''
    )

    return f'{label}\n{rest}\n<div class="clf-value">{value}</div>'.strip()


def _value(block):
    values = block['values']

    if not values:
        return f'<p class="clf-empty">{NOT_ANSWERED}</p>'

    if is_verbatim(block):
        # Keep line breaks and alignment of pasted command output intact.
        return f'<pre><code>{_escape(verbatim(values))}</code></pre>'

    if len(values) == 1:
        return f'<p>{_escape(values[0])}</p>'

    items = '\n'.join(f'<li>{_escape(value)}</li>' for value in values)

    return f'<ul>\n{items}\n</ul>'


def _note_html(content, level):
    style = ' clf-note-warning' if level in ('error', 'warning') else ''

    return f'<div class="clf-note{style}">{_escape(content)}</div>'


def _reference(block, writer):
    extra = []

    if block['description']:
        extra.append(writer.render(block['description']))

    extra.append(
        f'<p class="clf-reference-path">Checklist: <code>{_escape(block["path"])}</code></p>'
    )

    item = _item(
        writer, block['label'], marker(block['checked']), block['required'], extra=extra
    )

    return f'<ul class="clf-checklist clf-reference">\n{item}\n</ul>'
