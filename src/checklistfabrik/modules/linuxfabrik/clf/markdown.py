"""
ChecklistFabrik text_output module

This module renders Jinja templated markdown to HTML.

EXAMPLE::

    - linuxfabrik.clf.markdown:
        content: |
            ### Markdown Support

            ChecklistFabrik supports *Markdown*!
"""

import jinja2
import mistune


def main(**kwargs):
    rendered_html = mistune.html(
        jinja2.Template(kwargs['content']).render(**kwargs),
    )

    return {
        'html': f'<div class="form-label">{rendered_html}</div>',
    }
