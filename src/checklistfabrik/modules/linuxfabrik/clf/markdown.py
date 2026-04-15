"""
ChecklistFabrik Markdown module

This module renders Jinja templated Markdown to HTML.

EXAMPLE::

    - linuxfabrik.clf.markdown:
        content: |
            ### Markdown Support

            ChecklistFabrik supports *Markdown*!
"""


def main(**kwargs):
    # Content is rendered with the autoescape-free Jinja environment because
    # Mistune performs its own HTML escaping on the resulting text. Rendering
    # through the autoescape environment would double-escape fact values that
    # contain characters such as `"` (autoescape to `&#34;`, then Mistune to
    # `&amp;#34;`).
    clf_jinja_env_plain = kwargs['clf_jinja_env_plain']
    clf_markdown = kwargs['clf_markdown']

    rendered_html = clf_markdown(
        clf_jinja_env_plain.from_string(kwargs['content']).render(**kwargs),
    )

    return {
        'html': f'<div class="clf-markdown-block">{rendered_html}</div>',
    }
