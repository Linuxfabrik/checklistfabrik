"""
ChecklistFabrik text_output module

This module renders Jinja templated markdown to HTML.

EXAMPLE::

    - linuxfabrik.clf.markdown:
        content: |
            ### Markdown Support

            ChecklistFabrik supports *Markdown*!
"""


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_markdown = kwargs['clf_markdown']

    rendered_html = clf_markdown(
        clf_jinja_env.from_string(kwargs['content']).render(**kwargs),
    )

    return {
        'html': f'<div class="form-label">{rendered_html}</div>',
    }
