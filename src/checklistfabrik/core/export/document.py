"""Turn a loaded checklist into the neutral document that the exporters render.

The document is a plain dictionary so it can be inspected, tested and serialised without
pulling in any of the exporters:

    {
        'description': str,        # checklist description, plain text
        'generator': str | None,   # generator metadata, None if it was switched off
        'pages': [
            {
                'applicable': bool,        # False if the page was excluded by `when`
                'tasks': [
                    {
                        'applicable': bool,
                        'blocks': [...],   # see `checklistfabrik.core.export.blocks`
                        'module': str,
                        'when': str | None,
                    },
                ],
                'title': str,              # plain text
                'when': str | None,
            },
        ],
        'source': str | None,      # file name of the report the document was built from
        'stats': {'complete': bool, 'done': int, 'percent': int, 'total': int},
        'title': str,              # plain text
        'version': str | None,
    }
"""

import datetime

import jinja2

from .. import __version__, templates


def create_export_environment(template_loader=None):
    """Build the Jinja environment used while exporting.

    Autoescaping is off on purpose: the exporters escape for their own target markup, and
    an HTML-escaped value would end up as a literal `&amp;` in a reStructuredText or
    AsciiDoc document.
    """

    # The rendered text is never served as HTML: every exporter escapes for its own target
    # markup, and the HTML exporter escapes each value it writes.
    template_env = jinja2.Environment(  # nosec B701
        autoescape=False,
        loader=template_loader or templates.get_template_loader(),
    )
    template_env.globals['now'] = datetime.datetime.now

    return template_env


def build_document(checklist, source=None, include_metadata=True):
    """Build the neutral document for a loaded checklist."""

    template_env = create_export_environment()

    pages = [page.export(checklist.facts, template_env) for page in checklist.pages]

    return {
        'description': template_env.from_string(checklist.description or '').render(
            **checklist.facts
        ),
        'generator': f'ChecklistFabrik v{__version__}' if include_metadata else None,
        'pages': pages,
        'source': source,
        'stats': count_progress(pages),
        'title': template_env.from_string(checklist.title).render(**checklist.facts),
        'version': checklist.version,
    }


def count_block(block):
    """Count the completed and the total number of items of a single block."""

    block_type = block.get('type')

    if block_type == 'checklist':
        items = block.get('items') or []
        return sum(1 for item in items if item.get('checked')), len(items)

    if block_type == 'field':
        return (1 if block.get('values') else 0), 1

    if block_type == 'reference':
        return (1 if block.get('checked') else 0), 1

    # Output-only blocks (Markdown, HTML, notes) carry nothing that can be completed.
    return 0, 0


def count_progress(pages):
    """Count the overall completion of all pages and tasks that are applicable."""

    done = 0
    total = 0

    for page in pages:
        if not page['applicable']:
            continue

        for task in page['tasks']:
            if not task['applicable']:
                continue

            for block in task['blocks']:
                block_done, block_total = count_block(block)
                done += block_done
                total += block_total

    return {
        'complete': total > 0 and done == total,
        'done': done,
        'percent': round(done * 100 / total) if total else 0,
        'total': total,
    }
