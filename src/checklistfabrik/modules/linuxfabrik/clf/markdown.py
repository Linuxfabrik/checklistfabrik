"""
ChecklistFabrik text_output module

This module renders Jinja templated markdown to HTML.

EXAMPLE::

    - linuxfabrik.clf.markdown:
        content: |
            ### Markdown Support

            ChecklistFabrik supports *Markdown*!
"""

import mistune


def main(**kwargs):
    clf_template_env = kwargs['clf_template_env']

    rendered_html = mistune.html(
        clf_template_env.from_string(kwargs['content']).render(**kwargs),
    )

    return {
        'html': f'<div class="form-label">{rendered_html}</div>',
    }
